from datetime import datetime

from oslo.config import cfg

from sentry.alarm import render
from sentry.openstack.common import log as logging
from sentry.openstack.common import importutils

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

alarm_opts = [
    cfg.ListOpt('alarm_driver_classes',
                default=["sentry.alarm.driver.base.LogAlarmDriver"],
                help="A list contains the class of alarm driver."),
    cfg.IntOpt('alarm_quiet_seconds',
               default=60,
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

    def should_fire(self, error_log):
        if error_log.on_process:
            LOG.debug("Errorlog: %s is on processed, do not set off." %
                      error_log)
            return False

        if error_log.log_level != 'critical':
            LOG.debug("Not 'critical' level, not set off. %s" % error_log)
            return False

        uuid = error_log.stats_uuid

        last_time = self.backlog.get(uuid)

        if last_time:
            max_time = CONF.alarm_quiet_seconds
            delta = datetime.now() - last_time
            if delta.seconds <= max_time:
                LOG.debug("Errorlog: %(error)s set off at %(time)s, "
                          "quiet range is %(quiet)s" %
                          {'error': error_log, 'time': last_time,
                           'quiet': max_time})
                return False

        # NOTE(gtt): If not set off, last time does not report in backlog.
        # FIXME(gtt): self.backlog will grow up infinitely.
        self.backlog[uuid] = datetime.now()

        # At last is OK.
        return True

    def alarm_error_log(self, error_log):
        """Set off alarm when receive error log."""
        if not self.should_fire(error_log):
            return

        LOG.info("Setting off errorlog: %s " % error_log)
        html = render.render_error_log(error_log)
        self._call_drivers('set_off', error_log.title, html)
