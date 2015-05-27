import urllib2
import base64

import eventlet

from sentry import cron
from sentry import config
from sentry.db import api as dbapi
from sentry.openstack.common import log as logging
from sentry.openstack.common import jsonutils

LOG = logging.getLogger(__name__)


@cron.cronjob(60 * 15)  # per 15 minute
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
