from sentry.api.v1 import app
from sentry.db.sqlalchemy import session
from sentry.api.bottle import request

route = app.app.route


@route('/setting', method='PUT')
def update():
    req_sql_debug = request.json.get('sql_debug')

    if req_sql_debug:
        session.enable_sql_debug()
    else:
        session.disable_sql_debug()

    return {'sql_debug': req_sql_debug}
