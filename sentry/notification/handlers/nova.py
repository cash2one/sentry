from sentry.openstack.common import log as logging

from sentry.db import models
from sentry.notification import handlers

LOG = logging.getLogger(__name__)


class Handler(handlers.MySQLHandler):
    def handle_message(self, msg):

        event = models.Event()

        event.service = 'nova'
        event.raw_json = msg
        try:
            event.token = msg.get('_context_auth_token')
            event.is_admin = msg.get('_context_is_admin')
            event.request_id = msg.get('_context_request_id')
            event.roles = msg.get('_context_roles')
            event.project_id = msg.get('_context_project_id')
            event.project_name = msg.get('_context_project_name')
            event.user_name = msg.get('_context_user_name')
            event.user_id = msg.get('_context_user_id')
            event.event_type = msg['event_type']
            event.message_id = msg['message_id']
            event.payload = msg['payload']
            event.level = msg['priority']
            event.publisher_id = msg['publisher_id']
            event.timestamp = msg['timestamp']
            event.remote_address = msg.get('_context_remote_address')
            event.catelog = msg.get('_context_service_catalog')
            event.object_id = self.object_id(msg)
            event.binary, event.hostname = self.get_binary_hostname(
                event.publisher_id)
            event = self.save_event(event)
        except Exception as ex:
            LOG.exception("Message invalid: %(ex)s\n"
                          "n%(msg)s" % {'ex': ex, 'msg': msg})

        return event

    def object_id(self, msg):
        if msg['event_type'] in ['scheduler.run_instance.start',
                                 'aggregate.create.start',
                                 'aggregate.create.end',
                                 'aggregate.addhost.start',
                                 'aggregate.addhost.end',
                                 'aggregate.removehost.start',
                                 'aggregate.removehost.end',
                                 'aggregate.delete.start',
                                 'aggregate.delete.end',
                                 'aggregate.updatemetadata.start',
                                 'aggregate.updatemetadata.end',
                                 'aggregate.updateprop.start',
                                 'aggregate.updateprop.end',
                                 'network.floating_ip.allocate',
                                 'network.floating_ip.deallocate',
                                 'add_host_to_aggregate',
                                 'remove_host_from_aggregate',
                                 'create_aggregate',
                                 'delete_aggregate',
                                 'scheduler.run_instance.end']:
            return None

        if msg['priority'] == 'ERROR':
            return None

        try:
            return msg['payload']['instance_id']
        except (TypeError, ValueError, KeyError):
            msg = ("No instance_id in payload in %s" % msg)
            LOG.exception(msg)
            return None
