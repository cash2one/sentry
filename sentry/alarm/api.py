from datetime import datetime

from oslo.config import cfg

from sentry import config
from sentry.alarm import render
from sentry.openstack.common import log as logging
from sentry.openstack.common import importutils
from sentry.openstack.common import lockutils
from sentry.openstack.common import timeutils


CONF = cfg.CONF
LOG = logging.getLogger(__name__)

alarm_opts = [
    cfg.ListOpt('alarm_driver_classes',
                default=["sentry.alarm.driver.mail.EmailDriver"],
                help="A list contains the class of alarm driver."),
    cfg.IntOpt('alarm_quiet_seconds',
               default=600,
               help="In quiet seconds the same alarm does not set off."),
]
CONF.register_opts(alarm_opts)


class AlarmTimer(object):
    """Keep tracker of last fire time."""

    def __init__(self, max_time):
        self.backlog = {}
        self.max_time = max_time

    def log_fire(self, uuid):
        self.backlog[uuid] = datetime.now()

    def can_fire(self, uuid):
        last_time = self.backlog.get(uuid)

        if last_time:
            delta = datetime.now() - last_time

            if delta.seconds <= self.max_time:
                return False

        # First time
        self.log_fire(uuid)
        return True


class AlarmJudge(object):
    """"Judge whether the exception should be fired."""

    def __init__(self):
        self.timer = AlarmTimer(CONF.alarm_quiet_seconds)

    def _in_shutup(self, exc_detail):
        now = timeutils.local_now()

        # NOTE(gtt): no shupup
        if not exc_detail.shutup_start or not exc_detail.shutup_end:
            return False

        if exc_detail.shutup_start <= now <= exc_detail.shutup_end:
            return True
        else:
            return False

    def can_fire(self, exception):
        if exception.on_process:
            LOG.debug("%s is on processed, do not set off." % exception)
            return False

        if self._in_shutup(exception):
            LOG.debug("%s in shutup periodic, do not set off" % exception)
            return False

        if not self.timer.can_fire(exception.uuid):
            LOG.debug("%s is in silent periodic, do not set off" % exception)
            return False

        return True


class AlarmAPI(object):
    """Parse database object by render, then calling driver to set off alarm.
    """

    def __init__(self):
        self._init_drivers()
        self.judge = AlarmJudge()

    def _init_drivers(self):
        self.drivers = []
        for class_ in CONF.alarm_driver_classes:
            self.drivers.append(importutils.import_object(class_))

    def _call_drivers(self, method, *args, **kwargs):
        """Iterator calling drivers' method."""
        for driver in self.drivers:
            func = getattr(driver, method)
            func(*args, **kwargs)

    def alarm_exception(self, exc_info_detail):

        # FIXME(gtt): Race condiction here. Future will be implemented
        # in queues.
        @lockutils.synchronized(exc_info_detail.uuid, 'sentry-alarm-')
        def _alarm_exception():
            if not self.judge.can_fire(exc_info_detail):
                return

            LOG.info("Setting off exception: %s" % exc_info_detail)

            env = config.get_config('env_name')
            hostname = exc_info_detail.hostname
            binary = exc_info_detail.binary

            title = ('%s | %s | %s' % (env,
                                       hostname,
                                       exc_info_detail.exc_value))
            html_content = render.render_exception(exc_info_detail)

            self._call_drivers('set_off', title, html_content,
                               env=env, hostname=hostname, binary=binary)

        _alarm_exception()

    def alarm_service_changed(self, hostname, binary, status):
        title = "%s:%s status change to: %s" % (hostname, binary, status)
        LOG.info("Alarm service status changed: %s" % title)
        content = title
        self._call_drivers('set_off', title, content)
