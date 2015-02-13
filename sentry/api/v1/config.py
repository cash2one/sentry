from sentry import config
from sentry.api.v1 import app
from sentry.api import http_exception
from sentry.api.bottle import request

route = app.app.route


@route('/configs', method='GET')
def index():
    return config.items()


@route('/configs', method='POST')
def update():
    if not request.json:
        raise http_exception.HTTPBadRequest('Not update content')

    # first check all key
    valid_keys = config.keys()
    for key in request.json.keys():
        if key not in valid_keys:
            raise http_exception.HTTPBadRequest("%s not a valid config." % key)

    for key, value in request.json.iteritems():
        config.set_config(key, value)

    return request.json
