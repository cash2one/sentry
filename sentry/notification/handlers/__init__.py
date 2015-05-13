from sentry.openstack.common import log
from sentry.db import api as dbapi

LOG = log.getLogger(__name__)


class MySQLHandler(object):

    def save_event(self, event):
        return dbapi.event_create(event)

    def get_binary_hostname(self, publisher):
        binary, hostname = publisher.split('.', 1)
        return binary, hostname
