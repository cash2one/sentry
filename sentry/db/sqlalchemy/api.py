import sys

from sqlalchemy import func
from sqlalchemy import Boolean, Integer
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
        event = models.Event(
            message_id=event.message_id,
            token=event.token,
            object_id=event.object_id,
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


def _normalize_search_dict(model, search_dict):
    new_search_dict = {}
    columns = getattr(model, '__table__').columns
    for key, value in search_dict.iteritems():
        column = columns[key]

        if isinstance(column.type, Boolean):
            if value.lower() in ('1', 't', 'true', 'on', 'y', 'yes'):
                new_value = True
            else:
                new_value = False

        elif isinstance(column.type, Integer):
            new_value = int(value)
        else:
            new_value = value
        new_search_dict[key] = new_value

    return new_search_dict


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


def _model_complict_query(model_object, search_dict=None, sorts=None):
    se = get_session()

    # failed fast
    if search_dict:
        _validate_search_dict(model_object, search_dict)
        search_dict = _normalize_search_dict(model_object, search_dict)

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
# exception informations
# --------------------------


def _refresh_exc_info_count(exc_info_id):
    """In case of race condition, not increase the number of error log count.
    """
    session = get_session()
    with session.begin():
        exc_info = session.query(models.ExcInfo). \
                    filter(models.ExcInfo.id == exc_info_id). \
                    first()
        count = session.query(models.ExcInfoDetail). \
                    filter(models.ExcInfoDetail.exc_info_id == exc_info_id). \
                    count()
        exc_info.count = count
        session.add(exc_info)


def exc_info_get_all(search_dict=None, sorts=None):
    return _model_complict_query(models.ExcInfo, search_dict, sorts)


def exc_info_get_by_uuid(uuid):
    return exc_info_get_all({'uuid': uuid}).first()


def exc_info_update(uuid, values):
    if not isinstance(values, dict):
        raise ValueError()

    session = get_session()
    with session.begin():
        exc_info = session.query(models.ExcInfo). \
                filter(models.ExcInfo.uuid == uuid). \
                first()

        for key, value in values.iteritems():
            setattr(exc_info, key, value)

        session.add(exc_info)

    return exc_info


def exc_info_detail_get_by_uuid_and_number(uuid, number=1):
    session = get_session()

    exc_info = session.query(models.ExcInfo). \
                filter(models.ExcInfo.uuid == uuid). \
                first()
    if not exc_info:
        return None

    try:
        query = session.query(models.ExcInfoDetail). \
                    options(joinedload('exc_info')). \
                    filter(models.ExcInfoDetail.exc_info_id == exc_info.id)
        return query[number - 1]
    except IndexError:
        return None


def _exc_info_detail_get_by_id(id_):
    session = get_session()
    detail = session.query(models.ExcInfoDetail). \
            filter(models.ExcInfoDetail.id == id_). \
            options(joinedload('exc_info')). \
            first()
    return detail


def exc_info_detail_create(hostname, payload, binary, exc_class, exc_value,
                           file_path, func_name, lineno, created_at):
    session = get_session()

    with session.begin(subtransactions=True):
        #FIXME: Race condiction here. If two error log arrive at the same time.
        #The result will be two error stats with the same log_level and title.
        exc_info = session.query(models.ExcInfo). \
                filter(models.ExcInfo.exc_class == exc_class). \
                filter(models.ExcInfo.file_path == file_path). \
                filter(models.ExcInfo.func_name == func_name). \
                filter(models.ExcInfo.lineno == lineno). \
                first()
        if not exc_info:
            # First time to create
            exc_info = models.ExcInfo(
                binary=binary,
                count=0,
                on_process=False,
                uuid=utils.get_uuid(),
                exc_class=exc_class,
                file_path=file_path,
                func_name=func_name,
                lineno=lineno
            )

        exc_info.last_time = created_at
        session.add(exc_info)

        exc_detail = models.ExcInfoDetail(
            created_at=created_at,
            hostname=hostname,
            exc_value=exc_value,
            payload=payload
        )
        exc_detail.exc_info = exc_info
        session.add(exc_detail)

    _refresh_exc_info_count(exc_info.id)

    # Got latest exception detail
    return _exc_info_detail_get_by_id(exc_detail.id)

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
