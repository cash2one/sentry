from sentry.api.bottle import request
from sentry.api.web.app import route
from sentry.api.v1 import statsd
from sentry.templates import jinja

NS = 'openstack'
HTTP_API = 'http_api'


@route('/metrics')
def metric_http():
    hour = int(request.query.get('h', 1))
    d1 = statsd.metric(NS, HTTP_API, 'all', 'http_rt_mean', hour)
    d2 = statsd.metric(NS, HTTP_API, 'all', 'http_rt_upper_90', hour)
    d3 = statsd.metric(NS, HTTP_API, 'all', 'http_rt_upper', hour)

    d4 = statsd.metric(NS, HTTP_API, 'all', 'http_2xx', hour)
    d5 = statsd.metric(NS, HTTP_API, 'all', 'http_4xx', hour)
    d6 = statsd.metric(NS, HTTP_API, 'all', 'http_5xx', hour)

    latest = statsd.latest(NS, HTTP_API)['metrics']

    return jinja.render(
        'metric_api.html',
        data1=d1, data2=d2, data3=d3, data4=d4, data5=d5, data6=d6,
        latest=latest,
    )
