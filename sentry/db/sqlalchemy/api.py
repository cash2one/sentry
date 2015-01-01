import sys

from sentry.db.sqlalchemy import session
from sentry.db.sqlalchemy import models
from sentry.openstack.common import jsonutils


def get_backend():
    return sys.modules[__name__]


def event_create(event):
    se = session.get_session()

    # dump to json
    raw_json = jsonutils.dumps(event.raw_json)
    raw_message = models.RawMessage(json=raw_json)
    se.add(raw_message)

    event = models.Event(
        message_id=event.message_id,
        token=event.token,
        object_id=event.object_id,
        raw_message=raw_message,
        is_admin=event.is_admin,
        request_id=event.request_id,
        roles=jsonutils.dumps(event.roles),  # json
        project_id=event.project_id,
        project_name=event.project_name,
        user_name=event.user_name,
        user_id=event.user_id,
        event_type=event.event_type,
        payload=jsonutils.dumps(event.payload),  # json
        level=event.level,
        publisher_id=event.publisher_id,
        remote_address=event.remote_address,
        timestamp=event.timestamp,
        service=event.service,
        binary=event.binary,
        hostname=event.hostname,
    )
    se.add(event)
    se.commit()


def event_get_all():
    pass
