from sentry.openstack.common.db import api as db_api

_BACKEND_MAPPING = {'sqlalchemy': 'sentry.db.sqlalchemy.api'}

IMPL = db_api.DBAPI(backend_mapping=_BACKEND_MAPPING)


def event_create(event):
    return IMPL.event_create(event)


def event_get_all(*args, **kwargs):
    return IMPL.event_get_all(*args, **kwargs)


def event_schema(*args, **kwargs):
    return IMPL.event_schema(*args, **kwargs)
