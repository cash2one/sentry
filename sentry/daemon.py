import sys
import time
import signal
import eventlet
import multiprocessing
import logging as std_logging

from oslo.config import cfg

from sentry import cron
from sentry.notification import manager as notification_manager
from sentry.monitor import manager as monitor_manager
from sentry.openstack.common import log as logging

CONF = cfg.CONF
CONF.import_opt('watch_interval', 'sentry.crons.platform_watcher',
                group='platform_watcher')
LOG = logging.getLogger(__name__)
#TODO: close children process's STDIO, STDOUT, STDERR


def monkey_patch():
    eventlet.monkey_patch(os=False)


class NotificationProcess(multiprocessing.Process):
    log = logging.getLogger('notification_process')

    def run(self):
        self.log.info("Start running.")
        monkey_patch()

        notification = notification_manager.Manager()
        notification.setup_consumers()
        notification.consume_in_thread()
        notification.wait()


class MonitorProcess(multiprocessing.Process):
    log = logging.getLogger('monitor_process')

    def run(self):
        self.log.info("Start monitoring.")
        monkey_patch()

        monitor = monitor_manager.ServiceManager()
        monitor.start()


class CronProcess(multiprocessing.Process):
    log = logging.getLogger('cron_process')

    def run(self):
        self.log.info("Staring cron jobs.")
        monkey_patch()

        cron_engine = cron.CronEngine()
        cron_engine.register(cron.subscribe_oslist, None, 60 * 15)
        cron_engine.register(cron.watch_platform_status, None,
                             CONF.platform_watcher.watch_interval)
        cron_engine.wait()


class ProcessMaster(object):
    """Monitoring child process, respawn them if they die."""

    def __init__(self):
        CONF.log_opt_values(LOG, std_logging.DEBUG)
        self._running = False

    def start(self):

        self._spawn_notification()
        self._spawn_monitor()
        self._spawn_cron()

        self._running = True

        signal.signal(signal.SIGTERM, self._kill_handler)
        signal.signal(signal.SIGCHLD, self._kill_children_handler)

    def _spawn_notification(self):
        self.notification_process = NotificationProcess()
        self.notification_process.daemon = True
        self.notification_process.start()

    def _spawn_monitor(self):
        self.monitor_process = MonitorProcess()
        self.monitor_process.daemon = True
        self.monitor_process.start()

    def _spawn_cron(self):
        self.cron_process = CronProcess()
        self.cron_process.daemon = True
        self.cron_process.start()

    def _kill_notification(self):
        if self.notification_process.is_alive():
            LOG.info("Kill notification process")
            self.notification_process.terminate()

    def _kill_monitor(self):
        if self.monitor_process.is_alive():
            LOG.info("Kill monitor process")
            self.monitor_process.terminate()

    def _kill_cron(self):
        if self.cron_process.is_alive():
            LOG.info("Kill cron process")
            self.cron_process.terminate()

    def _kill_handler(self, signum, frame):
        LOG.info("Receive signal: %s. Exit nicely..." % signum)

        signal.signal(signum, signal.SIG_DFL)

        # Do not respawn child process
        self._running = False

        self._kill_notification()
        self._kill_monitor()
        self._kill_cron()

        self.notification_process.join()
        self.monitor_process.join()
        self.cron_process.join()

        sys.exit(0)

    def _kill_children_handler(self, signum, frame):
        if self._running:
            if not self.monitor_process.is_alive():
                LOG.warn("monitoring process was dead.")
                # Do not spawn too quickly.
                time.sleep(1.5)
                self._spawn_monitor()

            if not self.notification_process.is_alive():
                LOG.warn("notification process was dead.")
                # Do not spawn too quickly.
                time.sleep(1.5)
                self._spawn_notification()

            if not self.cron_process.is_alive():
                LOG.warn("cron process was dead.")
                # Do not spawn too quickly.
                time.sleep(1.5)
                self._spawn_cron()

    def wait(self):
        while True:
            try:
                signal.pause()
            except KeyboardInterrupt:
                self._kill_handler(signal.SIGINT, None)
