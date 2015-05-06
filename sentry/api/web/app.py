import os

import sentry
from sentry.api import utils
from sentry.api import bottle


app = utils.create_bottle_app()
route = app.route

static_path = os.path.join(os.path.dirname(sentry.__file__),
                           'static')


@route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root=static_path)
