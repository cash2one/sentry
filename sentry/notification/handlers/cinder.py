from sentry.openstack.common import log as logging

from sentry.notification import handlers
from sentry.db import models

LOG = logging.getLogger(__name__)


class Handler(handlers.MySQLHandler):
    def handle_message(self, msg):
        event = models.Event()
        event.service = 'cinder'

        event.raw_json = msg
        try:
            event.token = msg['_context_auth_token']
            event.is_admin = msg['_context_is_admin']
            event.request_id = msg['_context_request_id']
            event.roles = msg['_context_roles']
            event.project_id = msg['_context_project_id']
            event.project_name = msg['_context_project_name']
            # FIXME:find a way to inject user_name into cinder
            # event.user_name = msg['_context_user_name']
            event.user_id = msg['_context_user_id']
            event.event_type = msg['event_type']
            event.message_id = msg['message_id']
            event.payload = msg['payload']
            event.level = msg['priority']
            event.publisher_id = msg['publisher_id']
            event.timestamp = msg['timestamp']
            event.remote_address = msg['_context_remote_address']
            event.catelog = msg['_context_service_catalog']
            event.object_id = self.object_id(msg)

            # The publisher_id of volume_type.delete/start is 'volumeType'
            if not event.event_type.startswith('volume_type'):
                event.binary, event.hostname = event.publisher_id.split('.')
            event = self.save_event(event)
            return event
        except Exception as ex:
            LOG.exception("Message invalid: %(ex)s\n"
                          "n%(msg)s" % {'ex': ex, 'msg': msg})

    def object_id(self, msg):
        event_type = msg['event_type']

        if event_type == 'volume_type.delete' and msg['priority'] == 'ERROR':
            return msg['payload']['id']
        elif event_type in ['volume_type.create',
                            'volume_type.delete']:
            return None

        return msg['payload'].get('volume_id')
