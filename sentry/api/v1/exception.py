from sentry.api import utils
from sentry.api import http_exception
from sentry.api.bottle import request
from sentry.api.v1 import app as v1app
from sentry.db import api as dbapi


route = v1app.route


def exception_viewer(page):
    ret = page.to_dict()

    excs = []
    for exc in page:
        formatted_exc = {}
        formatted_exc['id'] = exc.uuid
        formatted_exc['count'] = exc.count
        formatted_exc['exception_name'] = exc.title
        formatted_exc['last_time'] = exc.datetime
        formatted_exc['on_process'] = exc.on_process
        excs.append(formatted_exc)

    ret['exceptions'] = excs
    return ret


@route('/exceptions/', method='GET')
@route('/exceptions', method='GET')
def index():
    try:
        query = utils.RequestQuery(request)
        db_query = dbapi.error_log_stats_get_all(query.search_dict,
                                                 query.sort)
        paginator = utils.Paginator(db_query, query.limit)
        page = paginator.page(query.page_num)
    except ValueError as ex:
        msg = str(ex)
        raise http_exception.HTTPBadRequest(msg)

    return exception_viewer(page)


@route('/exceptions/schema', method='GET')
@route('/exceptions/schema/', method='GET')
def schema():
    fields, sortables, searchable = dbapi.error_log_stats_schema()
    ret = {
        "schema": {
            #FIXME: not return fields here
            "searchable": searchable,
            "sortable": sortables,
        }
    }

    return ret


def format_frames(exc):
    frames = []
    for f in exc.frames:
        x = {
            'function': f.name,
            'vars': f.local_vars,
            'filename': f.filename,
            'context_line': f.context_line,
            'lineno': f.lineno,
        }
        frames.append(x)
    return frames


def format_error(error):
    ret = {}
    ret['count'] = error.count
    ret['meta'] = {
        'hostname': error.hostname,
        'service': error.sentry_payload.binary_name,
        'exception_name': error.title,
        'timestamp': error.datetime,
        "level": error.log_level,
        "logger": error.sentry_payload.name
    }
    ret['extra'] = error.sentry_payload.extra

    exc = error.sentry_payload.exception
    ret['exception'] = {
        'type': exc.exc_class,
        'value': exc.exc_value,
        'Location': error.sentry_payload.pathname,
        'frames': format_frames(exc)
    }
    return ret


@route('/exceptions/<uuid>', method='GET')
def detail(uuid):
    query = utils.RequestQuery(request)
    number = query.search_get_int('number', 1)
    error = dbapi.error_log_get_by_uuid_and_number(uuid, number)
    if error is None:
        raise http_exception.HTTPNotFound()
    return format_error(error)


@route('/exceptions/web/<uuid>', method='GET')
def detail_html(uuid):
    query = utils.RequestQuery(request)
    number = query.search_get_int('number', 1)
    error = dbapi.error_log_get_by_uuid_and_number(uuid, number)
    if error is None:
        raise http_exception.HTTPNotFound()
    from sentry.alarm import render
    return render.render_error_log(error)
