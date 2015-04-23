from sentry.openstack.common.db import api as db_api

_BACKEND_MAPPING = {'sqlalchemy': 'sentry.db.sqlalchemy.api'}

IMPL = db_api.DBAPI(backend_mapping=_BACKEND_MAPPING)


def event_create(event):
    return IMPL.event_create(event)


def event_get_all(*args, **kwargs):
    return IMPL.event_get_all(*args, **kwargs)


def event_schema(*args, **kwargs):
    return IMPL.event_schema(*args, **kwargs)


def exc_info_get_all(*args, **kwargs):
    return IMPL.exc_info_get_all(*args, **kwargs)


def exc_info_get_by_uuid(*args, **kwargs):
    return IMPL.exc_info_get_by_uuid(*args, **kwargs)


def exc_info_get_by_hash_str(*args, **kwargs):
    return IMPL.exc_info_get_by_hash_str(*args, **kwargs)


def exc_info_update(*args, **kwargs):
    return IMPL.exc_info_update(*args, **kwargs)


def exc_info_detail_get_by_uuid_and_number(*args, **kwargs):
    return IMPL.exc_info_detail_get_by_uuid_and_number(*args, **kwargs)


def exc_info_get_hash_str(*args, **kwargs):
    return IMPL.exc_info_get_hash_str(*args, **kwargs)


def exc_info_detail_create(*args, **kwargs):
    return IMPL.exc_info_detail_create(*args, **kwargs)


def config_get_by_key(*args, **kwargs):
    return IMPL.config_get_by_key(*args, **kwargs)


def config_set(*args, **kwargs):
    return IMPL.config_set(*args, **kwargs)


def config_get_all(*args, **kwargs):
    return IMPL.config_get_all(*args, **kwargs)


def service_status_create_or_update(*args, **kwargs):
    return IMPL.service_status_create_or_update(*args, **kwargs)


def service_status_get_all(*args, **kwargs):
    return IMPL.service_status_get_all(*args, **kwargs)


def service_history_create(*args, **kwargs):
    return IMPL.service_history_create(*args, **kwargs)


def service_history_note(*args, **kwargs):
    return IMPL.service_history_note(*args, **kwargs)


def service_history_get_all(*args, **kwargs):
    return IMPL.service_history_get_all(*args, **kwargs)
