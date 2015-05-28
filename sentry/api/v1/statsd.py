import datetime

from sentry.api.v1.app import route
from sentry import ncm
from sentry.db import api as dbapi
from sentry.openstack.common import timeutils
from sentry.openstack.common import jsonutils


def data_to_points(raw_data):
    if isinstance(raw_data, basestring):
        raw_data = jsonutils.loads(raw_data)

    metric_datas = raw_data['MetricData']['metricDatas']

    ret = []
    # creatTime eg. 1431703800000 is compatiable with javascript.
    for metric in metric_datas:
        ret.append([metric['createTime'], metric['average']])
    return ret


def get_period(request_period):
    """request_period unit is hour, return unit is minute."""
    if request_period <= 6:
        return 1
    elif request_period <= 12:
        return 2
    elif request_period <= 24:
        return 5
    elif request_period <= 3 * 24:
        return 15
    elif request_period <= 7 * 24:
        return 30
    else:
        return 3 * 60


@route('/metric/<ns>/<dimen_name>/<dimen_value>/<metric>/<hour:int>')
def metric(ns, dimen_name, dimen_value, metric, hour):
    """Return metric datas in recent hours.

    GET /v1/metric/openstack/http_api/all/http_rt_count/1
    GET /v1/metric/openstack/http_api/all/http_rt_mean/1
    """
    client = ncm.get_client()

    # Get future 2 minute data here
    end = timeutils.local_now() + datetime.timedelta(minutes=2)
    start = end - datetime.timedelta(hours=hour)

    period = get_period(hour)
    raw_data = client.get_metric_data(
        ns, metric, dimen_name, dimen_value, start, end, period
    )

    label = '%s.%s.%s.%s' % (ns, dimen_name, dimen_value, metric)
    return {
        'label': label,
        'data': data_to_points(raw_data),
    }


@route('/metric/status/<ns>/<dimen_name>')
def list(ns, dimen_name):
    """Return metric latest status.

    Make something like this:

        {
            'metrics': [
                {
                    "namespace": "openstack",
                    "dimension_name": "http_api",
                    "dimension_value": "all",
                    "metrics": {
                        "http_rt_count": 30.0,
                        "http_rt_mean": 10.0,
                        "http_rt_upper_90": 0.3
                    }
                },
                {
                    "namespace": "openstack",
                    "dimension_name": "http_api",
                    "dimension_value": "compute_get_all",
                    "metrics": {
                        "http_rt_count": 10.0,
                        "http_rt_mean": 9.0,
                        "http_rt_lower": 2.2
                    }
                }
            ]
        }
    """

    query = dbapi.metric_get_all({'namespace': ns, 'dimen_name': dimen_name})

    metrics = {}

    for metric in query.all():
        key = '%s_%s_%s' % (metric.namespace,
                            metric.dimen_name,
                            metric.dimen_value)
        if key not in metrics:
            # Create one
            metric_obj = {}
            metric_obj['namespace'] = metric.namespace
            metric_obj['dimension_name'] = metric.dimen_name
            metric_obj['dimension_value'] = metric.dimen_value
            metric_obj['metrics'] = {}
            metrics[key] = metric_obj

        metrics[key]['metrics'][metric.metric_name] = metric.metric_value

    return {'metrics': metrics.values()}
