"""
Eventlet based, cron like jobs.
"""
import time
import eventlet

from sentry import green
from sentry.openstack.common import log as logging

__all__ = [
    'get_engine', 'cronjob',
]
LOG = logging.getLogger(__name__)


class CronJob(object):
    """A wrapper about job for CronEngine."""

    def __init__(self, function, slow_start_s, interval_s):
        self.function = function
        self.slow_start_s = slow_start_s
        self.interval_s = interval_s

    def loopingcall(self):
        while True:
            if self.slow_start_s:
                eventlet.sleep(self.slow_start_s)

            start = time.time()
            try:
                self.function()
            except Exception:
                LOG.exception('')

            end = time.time()
            delta = end - start
            LOG.debug("%s finished in %s. sleep %s" %
                      (self.function, delta, self.interval_s))

            eventlet.sleep(self.interval_s)

    def __repr__(self):
        return '<Cronjob %s>' % self.function


class CronEngine(green.GreenletDaemon):
    """The Cronjob manager"""

    def __init__(self):
        self.pool = eventlet.GreenPool()
        self.functions = {}

    def register(self, function, slow_start_s, interval_s):
        """Register a job into engine. The job immediately start running.

        :param function: An callable object, like a function.
        :param slow_start_s: int, If given, the cron job will wait given
                            seconds before running.
        :param interval_s: int, the interval in seconds between each time.

        """
        LOG.debug("Loading cron job: %s, slow: %s, interval: %s" %
                  (function, slow_start_s, interval_s))
        job = CronJob(function, slow_start_s, interval_s)
        thread = self.pool.spawn(job.loopingcall)
        self.functions[job] = thread
        return thread

    def load_jobs(self, module='sentry.crons'):
        """Load cronjob from a module path."""
        # the __init__ of module will take care of real loading.
        __import__(module)


ENGINE = CronEngine()


def get_engine():
    return ENGINE


def cronjob(interval_s, slow_start=None):
    """A decoration to easily register a cronjob.

    Example:

        @cronjob(60, 10)
        def foo():
            pass

    The function foo() will wait about 10 second before the first time run.
    And when first time finished, wait about 60 second, then set off
    another time.
    """

    def wrapper(func):

        ENGINE.register(func, slow_start, interval_s)

        def inner(*args, **kwargs):
            func(*args, **kwargs)

        return inner

    return wrapper
