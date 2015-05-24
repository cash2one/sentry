from sentry.api.bottle import request
from sentry.api.web.app import route
from sentry.templates import jinja
from sentry.db import api as dbapi


@route('/services')
def index():
    services = dbapi.service_status_get_all().all()
    return jinja.render('services.html', services=services)


@route('/services/<hostname_binary>')
def detail(hostname_binary):
    hour = int(request.query.get('h', 1))
    service_name = hostname_binary
    metric_url = ('/v1/metric/openstack/service/%s/rpc_response_time/%s' %
                  (hostname_binary, hour))

    return jinja.render('services_flot.html',
                        hour=hour,
                        metric_url=metric_url,
                        service_name=service_name)


@route('/flot')
def flot():
    return jinja.render('flot.html')
