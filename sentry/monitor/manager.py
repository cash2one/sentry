import re

import eventlet
from oslo.config import cfg

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

    def process_failed(self, changed):
        pass

    def process_regain(self, changed):
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

    def push_ncm(self, status):
        from sentry import ncm

        ncmclient = ncm.get_client()
        if not ncmclient:
            LOG.warn("NCM Client is disabled, do not push metric.")
            return

        metric_value_map = {state.CHECK_OK: 0,
                            state.CHECK_TIMEOUT: 1,
                            state.CHECK_FAILED: 2}
        metric_name = 'service_status'
        metric_value = metric_value_map[status]
        dimension_name = 'service'
        dimension_value = '%s:%s' % (self.checker.hostname,
                                     self.checker.binary_name)
        ncmclient.post_metric(
            metric_name, metric_value, dimension_name,
            dimension_value,
            {'hostname': self.checker.hostname,
             'binary': self.checker.binary_name}
        )
        LOG.debug("Push to NCM successfully")

    def process_status(self, status):
        dbapi.service_status_create_or_update(
            self.checker.binary_name,
            self.checker.hostname,
            status,
        )
        changed = self._state.change_to(status)
        if changed:
            if (changed['old_state'] == state.CHECK_OK and
                            changed['new_state'] != state.CHECK_OK):
                self.process_failed(changed)
            elif (changed['old_state'] != state.CHECK_OK and
                            changed['new_state'] == state.CHECK_OK):
                self.process_regain(changed)
        self.last_status = status
        self.push_ncm(status)

    def _run_forever(self):
        while True:
            # Make sure run_forever will not break out
            try:
                status = self.checker.check_status()
                msg = '%s check result: %s, sleep %ss' % (self,
                                                          status,
                                                          self.interval_s)
                LOG.debug(msg)
                self.process_status(status)

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
    """The boss who controls the main monitor logic

    In this context, checker to service is one to one mapping.
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
