from sentry.openstack.common.db import api as db_api

_BACKEND_MAPPING = {'sqlalchemy': 'sentry.db.sqlalchemy.api'}

IMPL = db_api.DBAPI(backend_mapping=_BACKEND_MAPPING)


def event_create(event):
    return IMPL.event_create(event)


def event_get_all(*args, **kwargs):
    return IMPL.event_get_all(*args, **kwargs)


def event_schema(*args, **kwargs):
    return IMPL.event_schema(*args, **kwargs)


def error_log_create(errorlog):
    return IMPL.error_log_create(errorlog)


def error_log_stats_get_all(*args, **kwargs):
    return IMPL.error_log_stats_get_all(*args, **kwargs)


def error_log_stats_schema(*args, **kwargs):
    return IMPL.error_log_stats_schema(*args, **kwargs)


def error_log_get_by_uuid_and_number(*args, **kwargs):
    return IMPL.error_log_get_by_uuid_and_number(*args, **kwargs)
