from sentry.api.v1 import app
from sentry.api import utils
from sentry.api import http_exception
from sentry.api.bottle import request
from sentry.db import api as dbapi
from sentry.openstack.common import timeutils

route = app.route


def event_viewer(page):
    ret = page.to_dict()

    events = []
    for event in page.object_list:
        event_dict = event.to_dict()
        event_dict.pop('raw_message_id')
        event_dict.pop('token')
        event_dict['timestamp'] = timeutils.isotime(event_dict['timestamp'])
        events.append(event_dict)
    ret['events'] = events

    return ret


@route('/events', method='GET')
@route('/events/', method='GET')
def index():
    try:
        query = utils.RequestQuery(request)

        event_query = dbapi.event_get_all(query.search_dict, query.sort,
                                          query.start, query.end)

        paginator = utils.Paginator(event_query, query.limit)
        page = paginator.page(query.page_num)
    except ValueError as ex:
        msg = str(ex)
        raise http_exception.HTTPBadRequest(msg)

    return event_viewer(page)


@route('/events/schema', method='GET')
@route('/events/schema/', method='GET')
def schema():
    fields, sortables, searchable = dbapi.event_schema()
    ret = {
        "schema": {
            "fields": fields,
            # NOTE(gtt): When these fields changed, please notify
            # `hzshaochunfei@corp.netease.com`, they need to
            # change their codes.
            "searchable": searchable,
            "sortable": sortables,
        }
    }

    return ret
