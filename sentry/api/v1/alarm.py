# -*-coding:utf8 -*-
from sentry.api.v1 import app as v1app
from sentry.db import api as dbapi
from sentry.api.bottle import request
from sentry.api import utils
from sentry.api import http_exception


route = v1app.route

SORTABLE = [
    "title",
    "count",
]

SEARCHABLE = ["type"]
MAPPER = {"title": "exc_class"}


def exception_alarm_viewer(page):
    ret = page.to_dict()

    alarms = []
    for error in page:
        obj = {}
        obj['title'] = error.exc_class
        obj['uuid'] = error.uuid
        obj['count'] = error.count
        obj['enabled'] = not error.on_process
        alarms.append(obj)

    ret['alarms'] = alarms
    return ret


@route('/alarms')
def index():
    query = utils.RequestQuery(request, MAPPER, SORTABLE, SEARCHABLE)
    type_ = query.search_dict.pop('type', 'exception')

    if type_ == 'exception':
        traces = dbapi.exc_info_get_all(query.search_dict, query.sort)
        paginator = utils.Paginator(traces, query.limit)
        page = paginator.page(query.page_num)
        return exception_alarm_viewer(page)
    else:
        #FIXME: implement other type alarm.
        return utils.Paginator([], query.limit).page(1).to_dict()


@route('/alarms/action', method='POST')
def update():
    request_query = utils.RequestQuery(request)
    action = request_query.json_get('action')
    alarm_uuids = request_query.json_get('alarms')

    if action == 'enable':
        # failed early
        for uuid in alarm_uuids:
            if not dbapi.exc_info_get_all({'uuid': uuid}).first():
                msg = "alarm %s not existed" % uuid
                raise http_exception.HTTPBadRequest(msg)

        for uuid in alarm_uuids:
            dbapi.exc_info_update(uuid, {'on_process': False})

        return request.json

    elif action == 'disable':

        # failed early
        for uuid in alarm_uuids:
            if not dbapi.exc_info_get_all({'uuid': uuid}).first():
                msg = "alarm %s not existed" % uuid
                raise http_exception.HTTPBadRequest(msg)

        for uuid in alarm_uuids:
            dbapi.exc_info_update(uuid, {'on_process': True})

        return request.json
    else:
        msg = '"action" should be in [enable, disable]'
        raise http_exception.HTTPBadRequest(msg)


@route('/alarms/schema')
def schema():
    return {
        "schema": {
            "sortable": SORTABLE,
            "searchable": SEARCHABLE,
        }
    }
