# -*-coding:utf8 -*-
from sentry.api.v1 import app as v1app
from sentry.db import api as dbapi
from sentry.api.bottle import request
from sentry.api import utils
from sentry.api import http_exception


route = v1app.route


def exception_alarm_viewer(page):
    ret = page.to_dict()

    alarms = []
    for error in page:
        obj = {}
        obj['title'] = error.title
        obj['uuid'] = error.uuid
        obj['count'] = error.count
        obj['enabled'] = not error.on_process
        alarms.append(obj)

    ret['alarms'] = alarms
    return ret


@route('/alarms')
def index():
    query = utils.RequestQuery(request)
    type_ = query.search_dict.get('type', 'exception')

    if type_ == 'exception':
        traces = dbapi.error_log_stats_get_all({'log_level': 'critical'})
        paginator = utils.Paginator(traces, query.limit)
        page = paginator.page(query.page_num)
        return exception_alarm_viewer(page)
    else:
        #FIXME: implement other type alarm.
        return utils.Paginator([], query.limit).page(1).to_dict()


@route('/alarms/action', method='POST')
def update():
    try:
        action = request.json['action']
    except (KeyError, TypeError):
        msg = "Please specify 'action'."
        raise http_exception.HTTPBadRequest(msg)

    if action == 'enable':
        try:
            alarm_uuids = request.json['alarms']
        except (KeyError, TypeError):
            msg = 'Please specify alarms to enable.'
            raise http_exception.HTTPBadRequest(msg)

        # failed early
        for uuid in alarm_uuids:
            if not dbapi.error_log_stats_get_all({'uuid': uuid}).first():
                msg = "alarm %s not existed" % uuid
                raise http_exception.HTTPBadRequest(msg)

        for uuid in alarm_uuids:
            dbapi.error_log_stats_update_on_process(uuid, False)

        return request.json

    elif action == 'disable':
        try:
            alarm_uuids = request.json['alarms']
        except (KeyError, TypeError):
            msg = 'Please specify alarms to enable.'
            raise http_exception.HTTPBadRequest(msg)

        # failed early
        for uuid in alarm_uuids:
            if not dbapi.error_log_stats_get_all({'uuid': uuid}).first():
                msg = "alarm %s not existed" % uuid
                raise http_exception.HTTPBadRequest(msg)

        for uuid in alarm_uuids:
            dbapi.error_log_stats_update_on_process(uuid, True)

        return request.json
    else:
        msg = '"action" should be in [enable, disable]'
        raise http_exception.HTTPBadRequest(msg)


@route('/alarms/schema')
def schema():
    return {
        "schema": {
            "sortable": [],
            "searchable": [],
        }
    }
