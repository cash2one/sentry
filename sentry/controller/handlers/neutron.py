from sentry.openstack.common import log as logging

from sentry.db import models
from sentry.controller import handlers

LOG = logging.getLogger(__name__)


class Handler(handlers.MySQLHandler):
    def handle_message(self, msg):
        event = models.Event()
        event.service = 'neutron'

        event.raw_json = msg
        try:
            # event.token = msg['_context_auth_token']
            event.is_admin = msg['_context_is_admin']
            event.request_id = msg['_context_request_id']
            event.roles = msg['_context_roles']
            event.project_id = msg['_context_project_id']
            event.project_name = msg['_context_tenant_name']
            event.user_name = msg['_context_user_name']
            event.user_id = msg['_context_user_id']
            event.event_type = msg['event_type']
            event.message_id = msg['message_id']
            event.payload = msg['payload']
            event.level = msg['priority']
            event.publisher_id = msg['publisher_id']
            event.timestamp = msg['timestamp']
            # event.remote_address = msg['_context_remote_address']
            # event.catelog = msg['_context_service_catalog']

            event.object_id = self.object_id(msg)
            event.binary, event.hostname = event.publisher_id.split('.')
            event = self.save_event(event)
            return event
        except Exception as ex:
            LOG.exception("Message invalid: %(ex)s\n"
                          "n%(msg)s" % {'ex': ex, 'msg': msg})

    def object_id(self, msg):
        event_type = msg['event_type']

        if event_type in ['port.create.start',
                          'subnet.create.start',
                          'router.create.start',
                          'vpnservice.create.start',
                          'port.update.start',
                          'monitor.create.start',
                          'network.create.start']:
            return None

        #port, create, start
        resource, method, status = event_type.split('.')

        if method == 'delete':
            return msg['payload']['%s_id' % resource]

        payload = msg['payload']
        # 'id' in first object in payload
        try:
            return payload[payload.keys()[0]]['id']
        except KeyError as ex:
            LOG.exception("missing object_id. exception: %(ex)\n"
                          "%(msg)s" % {'ex': ex, 'msg': msg})
            return None
