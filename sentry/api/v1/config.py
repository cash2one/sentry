from sentry import config
from sentry.api.v1 import app
from sentry.api import http_exception
from sentry.api import utils
from sentry.api.bottle import request

route = app.app.route


@route('/configs', method='GET')
def index():
    return config.items()


@route('/configs', method='POST')
def update():
    query = utils.RequestQuery(request)
    json_body = query.json()

    # first check all key
    valid_keys = config.keys()
    for key in json_body.keys():
        if key not in valid_keys:
            raise http_exception.HTTPBadRequest("%s not a valid config." % key)

    for key, value in json_body.iteritems():
        config.set_config(key, value)

    return request.json
