from sentry.api.bottle import request
from sentry.api.web.app import route
from sentry.api.v1 import statsd
from sentry.templates import jinja

NS = 'openstack'
HTTP_API = 'http_api'
RPC_API = 'rpc_api'


@route('/metrics')
@route('/metrics/http')
def metric_http():
    hour = int(request.query.get('h', 1))
    d1 = statsd.metric(NS, HTTP_API, 'all', 'http_rt_mean', hour)
    d2 = statsd.metric(NS, HTTP_API, 'all', 'http_rt_upper_90', hour)
    d3 = statsd.metric(NS, HTTP_API, 'all', 'http_rt_upper', hour)

    d4 = statsd.metric(NS, HTTP_API, 'all', 'http_2xx', hour)
    d5 = statsd.metric(NS, HTTP_API, 'all', 'http_4xx', hour)
    d6 = statsd.metric(NS, HTTP_API, 'all', 'http_5xx', hour)
    d7 = statsd.metric(NS, HTTP_API, 'all', 'http_rt_count', hour)

    latest = statsd.latest(NS, HTTP_API)['metrics']

    return jinja.render(
        'metric_api.html',
        flot1_datas=[d1, d2, d3],
        flot2_datas=[d4, d5, d6, d7],
        latest=latest,
    )


@route('/metrics/rpc')
def metric_rpc():
    hour = int(request.query.get('h', 1))
    d1 = statsd.metric(NS, RPC_API, 'all', 'rpc_rt_mean', hour)
    d2 = statsd.metric(NS, RPC_API, 'all', 'rpc_rt_upper_90', hour)
    d3 = statsd.metric(NS, RPC_API, 'all', 'rpc_rt_upper', hour)

    d4 = statsd.metric(NS, RPC_API, 'all', 'rpc_rt_count', hour)
    d5 = statsd.metric(NS, RPC_API, 'all', 'rpc_error', hour)

    latest = statsd.latest(NS, RPC_API)['metrics']

    return jinja.render(
        'metric_rpc.html',
        flot1_datas=[d1, d2, d3],
        flot2_datas=[d4, d5],
        latest=latest,
    )
