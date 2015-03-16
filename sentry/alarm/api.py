from datetime import datetime

from oslo.config import cfg

from sentry import config
from sentry.alarm import render
from sentry.openstack.common import log as logging
from sentry.openstack.common import importutils
from sentry.openstack.common import lockutils


CONF = cfg.CONF
LOG = logging.getLogger(__name__)

alarm_opts = [
    cfg.ListOpt('alarm_driver_classes',
                default=["sentry.alarm.driver.base.LogAlarmDriver"],
                help="A list contains the class of alarm driver."),
    cfg.IntOpt('alarm_quiet_seconds',
               default=600,
               help="In quiet seconds the same alarm does not set off."),
]
CONF.register_opts(alarm_opts)


class AlarmAPI(object):
    """Parse database object by render, then calling driver to set off alarm.
    """

    def __init__(self):
        self._init_drivers()
        # cache last time of alarms
        self.backlog = {}

    def _init_drivers(self):
        self.drivers = []
        for class_ in CONF.alarm_driver_classes:
            self.drivers.append(importutils.import_object(class_))

    def _call_drivers(self, method, *args, **kwargs):
        """Iterator calling drivers' method."""
        for driver in self.drivers:
            func = getattr(driver, method)
            func(*args, **kwargs)

    def should_fire(self, exc_detail):
        # On process
        if exc_detail.on_process:
            LOG.debug("%s is on processed, do not set off." % exc_detail)
            return False

        # In silence
        uuid = exc_detail.uuid

        last_time = self.backlog.get(uuid)

        if last_time:
            max_time = CONF.alarm_quiet_seconds
            delta = datetime.now() - last_time
            if delta.seconds <= max_time:
                LOG.debug("Exception: %(error)s set off at %(time)s, "
                          "quiet range is %(quiet)s" %
                          {'error': exc_detail, 'time': last_time,
                           'quiet': max_time})
                return False

        # NOTE(gtt): If not set off, last time does not report in backlog.
        # FIXME(gtt): self.backlog will grow up infinitely.
        self.backlog[uuid] = datetime.now()

        # At last is OK.
        return True

    def alarm_exception(self, exc_info_detail):

        # FIXME(gtt): Race condiction here. Future will be implemented
        # in queues.
        @lockutils.synchronized(exc_info_detail.uuid, 'sentry-alarm-')
        def _alarm_exception():
            if not self.should_fire(exc_info_detail):
                return

            LOG.info("Setting off exception: %s" % exc_info_detail)
            title = ('%s | %s | %s' % (config.get_config('env_name'),
                                    exc_info_detail.hostname,
                                    exc_info_detail.exc_value))
            html_content = render.render_exception(exc_info_detail)
            self._call_drivers('set_off', title, html_content)

        _alarm_exception()
