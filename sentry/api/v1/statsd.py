import datetime

from sentry.api.v1.app import route
from sentry import ncm
from sentry.openstack.common import timeutils
from sentry.openstack.common import jsonutils


def data_to_points(raw_data):
    if isinstance(raw_data, basestring):
        raw_data = jsonutils.loads(raw_data)

    metric_datas = raw_data['MetricData']['metricDatas']

    ret = []
    # creatTime eg. 1431703800000 is compatiable with javascript.
    for metric in metric_datas:
        # Work around flot always think timestamp is UTC
        # we are in UTC +8
        timestamp = metric['createTime'] + 1000 * 60 * 60 * 8
        ret.append([timestamp, metric['average']])
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
