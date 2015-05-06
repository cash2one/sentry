from sentry.api.v1.app import route
from sentry.api import http_exception
from sentry.api.bottle import request
from sentry.api import utils
from sentry.db import api as dbapi


SEARCHABLE = [
    'binary',
    'state',
    'hostname',
]

SORTABLE = [
    "binary",
    "state",
    'hostname',
]

MAPPER = {}


def format_service_status(page):
    ret = page.to_dict()

    services = []
    for db_service in page.object_list:
        x = {}
        x['binary'] = db_service.binary
        x['state'] = db_service.state
        x['updated_at'] = db_service.updated_at
        x['hostname'] = db_service.hostname
        services.append(x)
    ret['services'] = services
    return ret


def format_history(db_history):
    x = {}
    x['binary'] = db_history.binary
    x['hostname'] = db_history.hostname
    x['start_at'] = db_history.start_at
    x['end_at'] = db_history.end_at
    x['duration'] = db_history.duration
    x['note'] = db_history.note
    x['id'] = db_history.id
    return x


def format_service_history(page):
    ret = page.to_dict()

    histories = []
    for db_history in page.object_list:
        histories.append(format_history(db_history))

    ret['histories'] = histories
    return ret


@route('/services')
def index():
    query = utils.RequestQuery(request, MAPPER, SORTABLE, SEARCHABLE)
    db_query = dbapi.service_status_get_all(query.search_dict, query.sort)
    page = utils.Paginator(db_query, query.limit).page(query.page_num)
    return format_service_status(page)


@route('/services/schema')
def service_schema():
    ret = {
        "schema": {
            "searchable": SEARCHABLE,
            "sortable": SORTABLE,
        }
    }
    return ret


H_SEARCHABLE = [
    'binary',
    'hostname',
]
H_SORTABLE = [
    "binary",
    'hostname',
]
H_MAPPER = {}


@route('/services/history')
def history():
    query = utils.RequestQuery(request, H_MAPPER, H_SORTABLE, H_SEARCHABLE)
    db_query = dbapi.service_history_get_all(
        query.search_dict, query.sort,
        query.start_datetime, query.end_datetime
    )
    page = utils.Paginator(db_query, query.limit).page(query.page_num)
    return format_service_history(page)


@route('/services/history/schema')
def history_schema():
    ret = {
        "schema": {
            "searchable": H_SEARCHABLE,
            "sortable": H_SORTABLE,
        }
    }
    return ret


@route('/services/history/<id>/note', method='POST')
def history_note(id):
    request_query = utils.RequestQuery(request)
    note = request_query.json_get('note')
    new_history = dbapi.service_history_note(id, note)
    if not new_history:
        raise http_exception.HTTPNotFound()
    return {'history': format_history(new_history)}
