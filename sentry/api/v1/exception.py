from sentry.api import utils
from sentry.api import http_exception
from sentry.api.bottle import request
from sentry.api.v1 import app as v1app
from sentry.db import api as dbapi


route = v1app.route

SEARCHABLE = ['on_process']
SORTABLE = ["count", "exception_name", 'last_time', 'on_process', 'service',
            'no']
MAPPER = {'exception_name': 'exc_class', 'service': 'binary',
          'no': 'id'}


def _format_exception(exception_info):
    exception_object = {
        'id': exception_info.uuid,
        'count': exception_info.count,
        'exception_name': exception_info.exc_class,
        'last_time': exception_info.last_time,
        'on_process': exception_info.on_process,
        'note': exception_info.note,
        'shutup_start': exception_info.shutup_start,
        'shutup_end': exception_info.shutup_end,
        'file_path': exception_info.file_path_cleaned,
        'func_name': exception_info.func_name,
        'no': exception_info.id,
        'exc_value': exception_info.exc_value,
        'service': exception_info.binary,
    }
    return exception_object


def _exception_viewer(page):
    ret = page.to_dict()

    excs = []
    for exc in page:
        formatted_exc = _format_exception(exc)
        excs.append(formatted_exc)

    ret['exceptions'] = excs
    return ret


@route('/exceptions/', method='GET')
@route('/exceptions', method='GET')
def index():
    try:
        query = utils.RequestQuery(request, MAPPER, SORTABLE, SEARCHABLE)
        db_query = dbapi.exc_info_get_all(query.search_dict, query.sort)
        paginator = utils.Paginator(db_query, query.limit)
        page = paginator.page(query.page_num)
    except ValueError as ex:
        msg = str(ex)
        raise http_exception.HTTPBadRequest(msg)

    return _exception_viewer(page)


@route('/exceptions/schema', method='GET')
@route('/exceptions/schema/', method='GET')
def schema():
    ret = {
        "schema": {
            "searchable": SEARCHABLE,
            "sortable": SORTABLE,
        }
    }

    return ret


def _format_frames(frames):
    frame_result = []
    for f in frames:
        x = {
            'function': f.name,
            'vars': f.local_vars,
            'filename': f.filename,
            'context_line': f.context_line,
            'lineno': f.lineno,
        }
        frame_result.append(x)
    return frame_result


def format_exception_detail(error):
    ret = {}
    ret['count'] = error.count
    ret['meta'] = {
        'hostname': error.hostname,
        'service': error.binary,
        'exception_name': error.exc_class,
        'timestamp': error.created_at,
        "level": error.spayload.levelname,
        "logger": error.spayload.module
    }
    ret['extra'] = error.spayload.extra

    ret['exception'] = {
        'type': error.exc_class,
        'value': error.exc_value,
        'Location': error.spayload.pathname,
        'frames': _format_frames(error.frames)
    }
    return ret


@route('/exceptions/<uuid>', method='GET')
def detail(uuid):
    query = utils.RequestQuery(request)
    number = query.search_get_int('number', 1)
    error = dbapi.exc_info_detail_get_by_uuid_and_number(uuid, number)
    if error is None:
        raise http_exception.HTTPNotFound()
    return format_exception_detail(error)


@route('/exceptions/<uuid>/note', method='POST')
def add_note(uuid):
    request_query = utils.RequestQuery(request)
    note = request_query.json_get('note')
    exception = dbapi.exc_info_get_by_uuid(uuid)
    if not exception:
        raise http_exception.HTTPNotFound()
    exception = dbapi.exc_info_update(uuid, {'note': note})
    return {'exception': _format_exception(exception)}


@route('/exceptions/noshutup', method='POST')
def no_shutup():
    request_query = utils.RequestQuery(request)
    uuids = request_query.json_get('uuids')

    # Validate uuids
    for uuid in uuids:
        if not dbapi.exc_info_get_by_uuid(uuid):
            msg = 'exception %s not existed' % uuid
            raise http_exception.HTTPBadRequest(msg)

    updateds = []
    for uuid in uuids:
        new_exception = dbapi.exc_info_update(
            uuid, {'shutup_start': None, 'shutup_end': None}
        )
        updateds.append(new_exception)

    exceptions = []
    for updated in updateds:
        exceptions.append(_format_exception(updated))

    response = {'exceptions': exceptions}
    return response


@route('/exceptions/shutup', method='POST')
def shutup():
    request_query = utils.RequestQuery(request)
    uuids = request_query.json_get('uuids')

    start_at = request_query.json_get('start_at')
    start_at = request_query.validate_timestr(start_at)

    end_at = request_query.json_get('end_at')
    end_at = request_query.validate_timestr(end_at)

    if end_at < start_at:
        msg = ("end_at: %s should over start_at: %s" % (end_at, start_at))
        raise http_exception.HTTPBadRequest(msg)

    # Validate uuids
    for uuid in uuids:
        if not dbapi.exc_info_get_by_uuid(uuid):
            msg = 'exception %s not existed' % uuid
            raise http_exception.HTTPBadRequest(msg)

    updateds = []
    for uuid in uuids:
        new_exception = dbapi.exc_info_update(
            uuid, {'shutup_start': start_at, 'shutup_end': end_at}
        )
        updateds.append(new_exception)

    exceptions = []
    for updated in updateds:
        exceptions.append(_format_exception(updated))

    response = {'exceptions': exceptions}
    return response


@route('/exceptions/web/<uuid>', method='GET')
def detail_html(uuid):
    query = utils.RequestQuery(request)
    number = query.search_get_int('number', 1)
    error = dbapi.exc_info_detail_get_by_uuid_and_number(uuid, number)
    if error is None:
        raise http_exception.HTTPNotFound()
    from sentry.alarm import render
    return render.render_exception(error)
