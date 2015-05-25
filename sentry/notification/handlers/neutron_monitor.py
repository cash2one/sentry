from oslo.config import cfg

from sentry.db import api as dbapi
from sentry.openstack.common import log as logging


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class Handler(object):

    def __init__(self):
        pass

    def handle_message(self, message):
        if not self.can_handle(message):
            return
        self._handle(message)

    def can_handle(self, message):
        msg_type = message.get('event_type')

        if msg_type and msg_type.startswith('network.monitor'):
            return True
        else:
            LOG.warn("Unknown msg_type %s, can not process." % msg_type)
            return False

    def _handle(self, message):
        msg_type = message.get('event_type')
        payload = message.get('payload', {})
        hostname = payload.get('agent_host')
        uuid = payload.get('instance_id')

        if msg_type == 'network.monitor.port_down':
            LOG.info("port of instance %s is down!" % uuid)
            dbapi.instance_network_status_create_or_update(hostname, uuid,
                                                           'port_down')
        elif msg_type == 'network.monitor.port_recover':
            LOG.info("port of instance %s is recover!" % uuid)
            db_ins = dbapi.instance_network_status_get_all(
                search_dict={'uuid': uuid})
            db_ins.delete()
