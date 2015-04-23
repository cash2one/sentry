import eventlet
import logging as std_logging

from oslo.config import cfg

from sentry.notification import manager as notification_manager
from sentry.monitor import manager as monitor_manager
from sentry.openstack.common import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class GreenletDaemon(object):
    """Running notification and monitor in here."""

    def __init__(self):
        # After manager instantiated, some handler will be imported
        CONF.log_opt_values(LOG, std_logging.DEBUG)
        notification = notification_manager.Manager()
        notification.setup_consumers()
        notification.consume_in_thread()

        monitor = monitor_manager.ServiceManager()
        eventlet.spawn(monitor.start)

    def wait(self):
        try:
            self.daemon_thread = eventlet.spawn(self._loop)
            self.daemon_thread.wait()
        except KeyboardInterrupt:
            LOG.info("KeyboardInterrupt received, Exit.")

    def _loop(self):
        """A infinite loop to block the thread not exit."""
        while True:
            eventlet.sleep(0.1)
