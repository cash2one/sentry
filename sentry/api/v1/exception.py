from sentry.api import utils
from sentry.api import http_exception
from sentry.api.bottle import request
from sentry.api.v1 import app as v1app
from sentry.db import api as dbapi


route = v1app.route

SEARCHABLE = []
SORTABLE = ["count", "exception_name", 'last_time', 'on_process']
MAPPER = {'exception_name': 'exc_class'}


def exception_viewer(page):
    ret = page.to_dict()

    excs = []
    for exc in page:
        formatted_exc = {}
        formatted_exc['id'] = exc.uuid
        formatted_exc['count'] = exc.count
        formatted_exc['exception_name'] = exc.exc_class
        formatted_exc['last_time'] = exc.last_time
        formatted_exc['on_process'] = exc.on_process
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

    return exception_viewer(page)


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


def format_frames(frames):
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


def format_error(error):
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
        'frames': format_frames(error.frames)
    }
    return ret


@route('/exceptions/<uuid>', method='GET')
def detail(uuid):
    query = utils.RequestQuery(request)
    number = query.search_get_int('number', 1)
    error = dbapi.exc_info_detail_get_by_uuid_and_number(uuid, number)
    if error is None:
        raise http_exception.HTTPNotFound()
    return format_error(error)


@route('/exceptions/web/<uuid>', method='GET')
def detail_html(uuid):
    query = utils.RequestQuery(request)
    number = query.search_get_int('number', 1)
    error = dbapi.exc_info_detail_get_by_uuid_and_number(uuid, number)
    if error is None:
        raise http_exception.HTTPNotFound()
    from sentry.alarm import render
    return render.render_exception(error)
