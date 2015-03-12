from sentry.openstack.common import log
from sentry.db import api as dbapi

LOG = log.getLogger(__name__)


class MySQLHandler(object):

    def save_event(self, event):
        return dbapi.event_create(event)
