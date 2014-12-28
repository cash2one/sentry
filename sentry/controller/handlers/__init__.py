from sentry.openstack.common import log

LOG = log.getLogger(__name__)


class PersistentHandler(object):

    def save_notification(self, msg):
        msg_id = msg.get('message_id')
        msg_event_type = msg.get('event_type')
        LOG.debug("Processing message %(id)s, event_type: %(type)s" %
                  {'id': msg_id, 'type': msg_event_type})
        return mongo.raw_message_create(msg)

    def save_event(self, event):
        """Save to mongo db."""
        return mongo.event_create(event.to_dict())

    def save_unknown_event(self, event):
        return mongo.unknown_event_create(event)
