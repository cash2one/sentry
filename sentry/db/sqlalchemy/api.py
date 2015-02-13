import sys

from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import desc, asc

from sentry.common import utils
from sentry.db.sqlalchemy import session as db_session
from sentry.db.sqlalchemy import models
from sentry.openstack.common import jsonutils
from sentry.openstack.common import timeutils

get_session = db_session.get_session


def get_backend():
    return sys.modules[__name__]


def event_create(event):
    se = get_session()

    with se.begin():
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


def _validate_search_dict(model, search_dict):
    """
    Inspect search dict contains invalid key of model searchable.
    """
    can_search = model.get_searchable()
    for key in search_dict.keys():
        if not key in can_search:
            msg = ("search by %(key)s invalid, only support: %(can)s" %
                    {'key': key, 'can': can_search})
            raise ValueError(msg)


def _validate_sort_keys(model, sort_keys):
    """
    Inspect sort_keys is searchable in model, if not raise ValueError.
    Return a new list contains sqlalchemy sort criterion.
    """
    sorts_criterion = []
    can_sort = model.get_sortable()

    if not sort_keys:
        return []

    for key in sort_keys:
        if len(key) < 2:
            raise ValueError('sort by "%s" not support' % key)

        if key[0] == '-':
            neg = True
            key = key[1:]
        else:
            neg = False

        if not (key in can_sort):
            msg = ("sort by %(key)s invalid, only support: %(can)s" %
                   {'key': key, 'can': can_sort})
            raise ValueError(msg)

        criterion = desc(getattr(model, key)) if neg else \
                asc(getattr(model, key))

        sorts_criterion.append(criterion)
    return sorts_criterion


def _get_count(query):
    """Sqlalchemy count using subquery which is slow.

    :param model: should contains `id` field.
    """
    count_q = query.statement.with_only_columns([func.count()])
    count = query.session.execute(count_q).scalar()
    return count


def _model_complict_query(model_object, search_dict={}, sorts=[]):
    se = get_session()

    # failed fast
    if search_dict:
        _validate_search_dict(model_object, search_dict)

    sorts_criterion = _validate_sort_keys(model_object, sorts)

    query = se.query(model_object)

    if search_dict:
        query = query.filter_by(**search_dict)

    for sort in sorts_criterion:
        query = query.order_by(sort)

    return query


def event_get_all(search_dict={}, sorts=[], start=None, end=None):
    query = _model_complict_query(models.Event, search_dict, sorts)
    if start:
        query = query.filter(models.Event.timestamp >= start)

    if end:
        query = query.filter(models.Event.timestamp <= end)

    return query


def event_schema():
    fields = models.Event.get_fields()
    sortables = models.Event.get_sortable()
    searchable = models.Event.get_searchable()
    return fields, sortables, searchable

# ---------------------------
# error logs
# --------------------------


def _refresh_error_log_stats_count(error_stats_id):
    """In case of race condition, not increase the number of error log count.
    """
    session = get_session()
    with session.begin():
        stats = session.query(models.ErrorLogStats). \
                    filter(models.ErrorLogStats.id == error_stats_id). \
                    first()
        count = session.query(models.ErrorLog). \
                    filter(models.ErrorLog.stats_id == error_stats_id). \
                    count()
        stats.count = count
        session.add(stats)


def error_log_stats_get(title, level, session=None):
    """Searched by title and log_level"""
    if session is None:
        session = get_session()

    query = session.query(models.ErrorLogStats). \
                filter(models.ErrorLogStats.title == title). \
                filter(models.ErrorLogStats.log_level == level)
    return query.first()


def error_log_stats_get_all(search_dict={}, sorts=[]):
    return _model_complict_query(models.ErrorLogStats, search_dict, sorts)


def error_log_stats_update_on_process(uuid, on_process):
    session = get_session()
    with session.begin():
        stats = session.query(models.ErrorLogStats). \
                    filter(models.ErrorLogStats.uuid == uuid). \
                    first()
        stats.on_process = on_process
        session.add(stats)
    return stats


def error_log_stats_schema():
    fields = models.ErrorLogStats.get_fields()
    sortables = models.ErrorLogStats.get_sortable()
    searchable = models.ErrorLogStats.get_searchable()
    return fields, sortables, searchable


def error_log_get_by_uuid_and_number(uuid, number=1):
    session = get_session()

    stats = session.query(models.ErrorLogStats). \
                filter(models.ErrorLogStats.uuid == uuid). \
                options(joinedload('errors')). \
                first()
    if not stats:
        return None

    try:
        return stats.errors[number - 1]
    except IndexError:
        return None


def error_log_get_by_id(id_):
    session = get_session()
    error_log = session.query(models.ErrorLog). \
                    filter(models.ErrorLog.id == id_). \
                    options(joinedload('error_stats')). \
                    first()
    return error_log


def error_log_create(errorlog):
    session = get_session()

    with session.begin(subtransactions=True):
        #FIXME: Race condiction here. If two error log arrive at the same time.
        #The result will be two error stats with the same log_level and title.
        stats = error_log_stats_get(errorlog.title,
                                    errorlog.log_level,
                                    session)
        if not stats:
            # The first time to create error_log_stats
            stats = models.ErrorLogStats(uuid=utils.get_uuid(),
                                         title=errorlog.title,
                                         log_level=errorlog.log_level,
                                         datetime=errorlog.datetime,
                                         count=0,
                                         on_process=False)

        error_log = models.ErrorLog(datetime=errorlog.datetime,
                                    hostname=errorlog.hostname,
                                    payload=errorlog.payload)

        # NOTE(gtt): Why setting error_log.stats_id does not work?
        error_log.error_stats = stats
        session.add(error_log)

        stats.datetime = error_log.datetime
        session.add(stats)
        session.flush()

    _refresh_error_log_stats_count(stats.id)

    # return the persistented error_log
    return error_log_get_by_id(error_log.id)


# --------------------------------------------------------
# config database api
# --------------------------------------------------------


def config_get_by_key(key):
    se = get_session()

    obj = se.query(models.Config). \
            filter(models.Config.key == key). \
            with_lockmode('update'). \
            first()
    se.close()
    return obj


def config_set(key, value):
    se = get_session()

    obj = config_get_by_key(key)

    if obj is None:
        # creating
        with se.begin():
            obj = models.Config(key=key, value=value)
            se.add(obj)
    else:
        with se.begin():
            obj.value = value
            obj.updated_at = timeutils.utcnow()
            se.add(obj)

    return obj


def config_get_all():
    session = get_session()
    return session.query(models.Config).all()
