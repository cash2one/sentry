"""
Eventlet based, cron like jobs
"""
import urllib2
import eventlet
import base64

from sentry import green
from sentry.db import api as dbapi
from sentry import config
from sentry.openstack.common import log as logging
from sentry.openstack.common import jsonutils

LOG = logging.getLogger(__name__)


class CronJob(object):

    def __init__(self, function, slow_start_s, interval_s):
        self.function = function
        self.slow_start_s = slow_start_s
        self.interval_s = interval_s

    def loopingcall(self):
        while True:
            if self.slow_start_s:
                eventlet.sleep(self.slow_start_s)

            try:
                self.function()
            except Exception:
                LOG.exception('')

            eventlet.sleep(self.interval_s)

    def __repr__(self):
        return '<Cronjob %s>' % self.function


class CronEngine(green.GreenletDaemon):

    def __init__(self):
        self.pool = eventlet.GreenPool()
        self.functions = {}

    def register(self, function, slow_start_s, interval_s):
        job = CronJob(function, slow_start_s, interval_s)
        thread = self.pool.spawn(job.loopingcall)
        self.functions[job] = thread
        return thread


def subscribe_oslist():
    oelist_url = config.get_config('oelist_url')
    LOG.info("Fetching oelist from: %s" % oelist_url)

    for retry in xrange(5):
        try:
            oelist_base64_content = urllib2.urlopen(oelist_url).read()
            break
        except Exception as ex:
            LOG.error("Fetch oelist failed: %s, retry" % ex)
            eventlet.sleep(2 * retry)
            continue

    oelist_json = base64.decodestring(oelist_base64_content)
    oelist = jsonutils.loads(oelist_json)
    for error in oelist['oelist']:
        hash_str = error['hash_str']
        db_error = dbapi.exc_info_get_by_hash_str(hash_str)
        if db_error:
            LOG.debug("Error in hash_str: %s set on_process to True.")
            dbapi.exc_info_update(db_error.uuid, {'on_process': True})

    LOG.info("Subscribe oelist done.")
