import time
import re

import eventlet
from oslo.config import cfg

from sentry import ncm
from sentry.db import api as dbapi
from sentry.alarm import api as alarm_api
from sentry.monitor import checkers
from sentry.monitor import state
from sentry.openstack.common import log as logging
from sentry import rabbit_admin

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

monitor_opts = [
    cfg.BoolOpt("enabled", default=False,
            help="Whether enable OpenStack RPC probering."),
    cfg.IntOpt("refresh_interval", default=30,
            help="The interval in seconds monitor fetchs queues from rabbit"),
    cfg.IntOpt("prober_interval", default=20,
            help="The interval in seconds prober openstack service"),
]
CONF.register_opts(monitor_opts, 'monitor')


class Prober(object):
    """Prober periodic call `checker` to probe service's health"""

    def __init__(self, service_checker):
        self.checker = service_checker
        self.interval_s = CONF.monitor.prober_interval
        self.last_status = None
        self.greenlet = None
        self.running = False
        self._state = state.StateMachine()
        self.alarm_api = alarm_api.AlarmAPI()

    def stop(self):
        self.greenlet.kill()
        self.running = False

    def start(self):
        LOG.debug("Start prober %s" % self)
        self.greenlet = eventlet.spawn(self._run_forever)
        eventlet.sleep(0)
        self.running = True

    def on_service_failed(self, changed):
        self.alarm_api.alarm_service_changed(self.checker.hostname,
                                             self.checker.binary_name,
                                             changed['new_state'])

    def on_service_recovered(self, changed):
        dbapi.service_history_create(
            self.checker.binary_name,
            self.checker.hostname,
            changed['start_at'],
            changed['end_at'],
            changed['duration'],
        )
        self.alarm_api.alarm_service_changed(self.checker.hostname,
                                             self.checker.binary_name,
                                             changed['new_state'])

    def push_to_ncm(self, response_time):
        ncm.push_rpc_response_time(response_time,
                                   self.checker.hostname,
                                   self.checker.binary_name)

    @staticmethod
    def _state_ok_to_other(changed):
        return (changed['old_state'] == state.CHECK_OK and
                changed['new_state'] != state.CHECK_OK)

    @staticmethod
    def _state_other_to_ok(changed):
        return (changed['old_state'] != state.CHECK_OK and
                changed['new_state'] == state.CHECK_OK)

    def process_status(self, status, response_time):
        """The main point to process status changes."""

        # Persistent to database
        dbapi.service_status_create_or_update(
            self.checker.binary_name,
            self.checker.hostname,
            status,
            response_time,
        )

        # process state changing
        changed = self._state.change_to(status)

        if changed:
            if self._state_ok_to_other(changed):
                self.on_service_failed(changed)
            elif self._state_other_to_ok(changed):
                self.on_service_recovered(changed)

        self.last_status = status
        self.push_to_ncm(response_time)

    def _run_forever(self):
        while True:
            # Make sure run_forever will not break out
            try:
                start = time.time()
                status = self.checker.check_status()
                end = time.time()
                response_time = end - start

                msg = ('%(name)s check result: %(status)s '
                       'duration: %(duration).3f, sleep %(sleep)ss' %
                       {'name': self, 'status': status,
                        'duration': response_time, 'sleep': self.interval_s})
                LOG.debug(msg)

                self.process_status(status, response_time)

            except Exception:
                msg = '%s check failed.' % self
                LOG.exception(msg)

            eventlet.sleep(self.interval_s)

    def __repr__(self):
        return '<Prober for %s>' % self.checker

    def __eq__(self, other):
        if type(other) is type(self):
            return self.checker == other.checker

    def __hash__(self):
        return hash(self.checker) ^ hash(self.__class__.__name__)


class ServiceManager(object):
    """The boss who controls the main monitoring logic.

    Under this context, checker to service is one to one mapping.
    """

    SERVICE_CHECK_MAPPER = [
        # Regexpress, service name, compoment name
        # nova
        (r'^scheduler\.(.*)$', checkers.NovaScheduler),
        (r'^compute\.(.*)$', checkers.NovaCompute),
        (r'^conductor\.(.*)$', checkers.NovaConductor),
        (r'^consoleauth\.(.*)$', checkers.NovaConsoleauth),
        # cinder
        (r'^cinder-scheduler:(.*)$', checkers.CinderScheduler),
        (r'^cinder-volume:(.*)$', checkers.CinderVolume),
        # neutron
        (r'^l3_agent\.(.*)$', checkers.NeutronL3Agent),
        (r'^dhcp_agent\.(.*)$', checkers.NeutronDHCPAgent),
        (r'^monitor_agent\.(.*)$', checkers.NeutronMonitorAgent),
        (r'^q-agent-notifier-l2population-update.\.(.*)$',
                                        checkers.NeutronOvsAgent),
    ]

    def __init__(self):
        self.rabbit_api = rabbit_admin.RabbitAPI()

        # The key is `checker`, value is `Prober`
        self.checker_prober_mapping = {}

        self.interval_s = CONF.monitor.refresh_interval

    def start(self):
        if not CONF.monitor.enabled:
            LOG.info("Monitor is disabled.")
            return
        while True:
            try:
                self._refresh_services()
            except Exception:
                LOG.exception('')

            eventlet.sleep(self.interval_s)

    def _get_services_set(self):
        services = []
        try:
            raw_queues = self.rabbit_api.get_queues()
        except Exception as ex:
            msg = 'Connect to RabbitMQ management failed: %s' % ex
            LOG.exception(msg)
            return []

        for queue in raw_queues:
            service = self._parse_queue_name(queue.name)
            if service:
                services.append(service)

        return services

    def _parse_queue_name(self, queue_name):
        for (pattern, service_cls) in self.SERVICE_CHECK_MAPPER:
            result = re.match(pattern, queue_name)
            if not result:
                continue

            hostname = result.group(1)
            return service_cls(hostname)

    @property
    def old_service_set(self):
        return self.checker_prober_mapping.keys()

    def _refresh_services(self):
        LOG.debug("Refresh services information.")
        services_set = self._get_services_set()
        LOG.debug("Got services %s" % services_set)

        for old in self.old_service_set:
            if old not in services_set:
                self._process_offline(old)

        for service in services_set:
            if service not in self.old_service_set:
                self._process_online(service)
        LOG.debug("Refresh service done.")

    def _process_online(self, service):
        LOG.info("Online service: %s" % service)
        prober = Prober(service)
        self.checker_prober_mapping[service] = prober
        prober.start()

    def _process_offline(self, service):
        LOG.info("Offline service: %s" % service)
        prober = self.checker_prober_mapping[service]
        prober.stop()
        del self.checker_prober_mapping[service]
