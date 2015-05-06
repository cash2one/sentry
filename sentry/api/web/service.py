from sentry.api.web.app import route
from sentry.templates import jinja
from sentry.db import api as dbapi


@route('/services')
def index():
    services = dbapi.service_status_get_all().all()
    return jinja.render('services.html', services=services)
