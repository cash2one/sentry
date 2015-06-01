from sentry.api.bottle import request
from sentry.api.web.app import route
from sentry.api.v1 import statsd
from sentry.templates import jinja

NS = 'openstack'
HTTP_API = 'http_api'
RPC_API = 'rpc_api'
DEFAULT_HOUR = 24


def _get_http_response_time_metric(dimen_name, dimen_value, hour):
    d1 = statsd.metric(NS, dimen_name, dimen_value, 'http_rt_mean', hour)
    d2 = statsd.metric(NS, dimen_name, dimen_value, 'http_rt_upper_90', hour)
    d3 = statsd.metric(NS, dimen_name, dimen_value, 'http_rt_upper', hour)
    return [d1, d2, d3]


def _get_http_request_per_minute_metric(dimen_name, dimen_value, hour):
    d4 = statsd.metric(NS, dimen_name, dimen_value, 'http_2xx', hour)
    d5 = statsd.metric(NS, dimen_name, dimen_value, 'http_4xx', hour)
    d6 = statsd.metric(NS, dimen_name, dimen_value, 'http_5xx', hour)
    d7 = statsd.metric(NS, dimen_name, dimen_value, 'http_rt_count', hour)
    return [d4, d5, d6, d7]


@route('/metrics/http/')
def metric_http():
    hour = int(request.query.get('h', DEFAULT_HOUR))
    api_name = 'all'
    rt_metrics = _get_http_response_time_metric(HTTP_API, api_name, hour)
    rpm_metrics = _get_http_request_per_minute_metric(HTTP_API, api_name, hour)

    latest = statsd.latest(NS, HTTP_API)['metrics']

    return jinja.render(
        'metric_http.html',
        hour=hour,
        api_name=api_name,
        flot1_datas=rt_metrics,
        flot2_datas=rpm_metrics,
        latest=latest,
    )


@route('/metrics/http/<api_name>/')
def metric_http_detail(api_name):
    hour = int(request.query.get('h', DEFAULT_HOUR))
    rt_metrics = _get_http_response_time_metric(HTTP_API, api_name, hour)
    rpm_metrics = _get_http_request_per_minute_metric(HTTP_API, api_name, hour)

    api_dimen = '%s@%s' % (HTTP_API, api_name)
    latest = statsd.latest(NS, api_dimen)['metrics']

    return jinja.render(
        'metric_http.html',
        hour=hour,
        api_name=api_name,
        flot1_datas=rt_metrics,
        flot2_datas=rpm_metrics,
        latest=latest,
    )


@route('/metrics/http/<api_name>/<host>/')
def metric_http_detail_at_host(api_name, host):
    hour = int(request.query.get('h', DEFAULT_HOUR))
    dimen_name = HTTP_API + '@' + api_name
    rt_metrics = _get_http_response_time_metric(dimen_name, host, hour)
    rpm_metrics = _get_http_request_per_minute_metric(dimen_name, host, hour)

    return jinja.render(
        'metric_http.html',
        hour=hour,
        api_name=api_name + '@' + host,
        flot1_datas=rt_metrics,
        flot2_datas=rpm_metrics,
    )


def _get_rpc_response_time_metric(dimen_name, dimen_value, hour):
    d1 = statsd.metric(NS, dimen_name, dimen_value, 'rpc_rt_mean', hour)
    d2 = statsd.metric(NS, dimen_name, dimen_value, 'rpc_rt_upper_90', hour)
    d3 = statsd.metric(NS, dimen_name, dimen_value, 'rpc_rt_upper', hour)
    return [d1, d2, d3]


def _get_rpc_request_per_minute_metric(dimen_name, dimen_value, hour):
    d4 = statsd.metric(NS, dimen_name, dimen_value, 'rpc_rt_count', hour)
    d5 = statsd.metric(NS, dimen_name, dimen_value, 'rpc_error', hour)
    return [d4, d5]


@route('/metrics/rpc/')
def metric_rpc():
    api = 'all'
    hour = int(request.query.get('h', DEFAULT_HOUR))
    rt_metrics = _get_rpc_response_time_metric(RPC_API, api, hour)
    rpm_metrics = _get_rpc_request_per_minute_metric(RPC_API, api, hour)

    latest = statsd.latest(NS, RPC_API)['metrics']

    return jinja.render(
        'metric_rpc.html',
        api_name=api,
        hour=hour,
        flot1_datas=rt_metrics,
        flot2_datas=rpm_metrics,
        latest=latest,
    )


@route('/metrics/rpc/<rpc_api>/')
def metric_rpc_detail(rpc_api):
    hour = int(request.query.get('h', DEFAULT_HOUR))
    rt_metrics = _get_rpc_response_time_metric(RPC_API, rpc_api, hour)
    rpm_metrics = _get_rpc_request_per_minute_metric(RPC_API, rpc_api, hour)

    rpc_dimen = '%s@%s' % (RPC_API, rpc_api)
    latest = statsd.latest(NS, rpc_dimen)['metrics']

    return jinja.render(
        'metric_rpc.html',
        api_name=rpc_api,
        hour=hour,
        flot1_datas=rt_metrics,
        flot2_datas=rpm_metrics,
        latest=latest,
    )


@route('/metrics/rpc/<rpc_api>/<host>/')
def metric_rpc_detail_at_host(rpc_api, host):
    hour = int(request.query.get('h', DEFAULT_HOUR))

    dimen_name = RPC_API + '@' + rpc_api

    rt_metrics = _get_rpc_response_time_metric(dimen_name, host, hour)
    rpm_metrics = _get_rpc_request_per_minute_metric(dimen_name, host, hour)

    return jinja.render(
        'metric_rpc.html',
        api_name=rpc_api + '@' + host,
        hour=hour,
        flot1_datas=rt_metrics,
        flot2_datas=rpm_metrics,
    )
