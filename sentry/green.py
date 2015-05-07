from eventlet import event
import eventlet

from sentry.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class GreenletDaemon(object):

    def wait(self):
        try:
            self.stop_event = event.Event()
            self.daemon_thread = eventlet.spawn(self._loop)
            self.daemon_thread.wait()
        except KeyboardInterrupt:
            LOG.info("KeyboardInterrupt received, Exit.")

    def _loop(self):
        """A infinite loop to block the thread not exit."""
        self.stop_event.wait()
