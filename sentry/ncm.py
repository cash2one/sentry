"""
NetEase Cloud Monitor python client.
"""

import time
import httplib
import hmac
import urllib
import hashlib
import json

from oslo.config import cfg

from sentry.common import retryutils
from sentry.openstack.common import log as logging
from sentry.openstack.common import timeutils

LOG = logging.getLogger(__name__)

CONF = cfg.CONF
ncm_opts = [
    cfg.StrOpt('ncm_host',
               help="NCM host. e.g, 127.0.0.1"),
    cfg.IntOpt('ncm_port', default=8186,
               help="NCM port, default is 8186."),
    cfg.StrOpt('ncm_namespace', default='openstack',
               help="The namespace when push metric data."),
    cfg.StrOpt('ncm_project_id', default='openstack_sentry',
               help="The project_id when push metric data."),
    cfg.StrOpt('ncm_access_key',
               help="The access key to access to NCM."),
    cfg.StrOpt('ncm_secret_key',
               help="The secret key to access to NCM."),
]
CONF.register_opts(ncm_opts)


class Monitor(object):
    """Send data to monitor server by accesskey authorization.
    """
    def __init__(self, monitor_service_host, monitor_service_port,
                project_id, namespace, access_key, access_secret):
        self.url = "%s:%s" % (monitor_service_host,
                              monitor_service_port)
        self.headers = {'Content-type': 'application/x-www-form-urlencoded'}
        self.project_id = project_id
        self.namespace = namespace
        self.access_key = access_key
        self.access_secret = access_secret

    def set_namespace(self, namespace):
        self.namespace = namespace

    @staticmethod
    def _java_timestamp(timestamp):
        return int(timestamp * 1000)

    def get_metric_data(self, namespace, metric_name,
                        dimension_key, dimension_value,
                        start, end, period_minute):
        """
        Get metric data points.

        :param start: datetime;
        :param end: datetime;
        :param period_minute: int, period in minute;

        The response look like:

           {
                "MetricData": {
                    "lable": "rpc_response_time",
                    "metricDatas": [
                        {
                            "sampleCount": 54,
                            "sum": 3.51,
                            "createTime": 1431703800000,
                            "maxinum": 2.03,
                            "average": 0.065,
                            "mininum": 0.013
                        },
                        {
                            "sampleCount": 90,
                            "sum": 2.83,
                            "createTime": 1431705600000,
                            "maxinum": 0.356,
                            "average": 0.031,
                            "mininum": 0.013
                        }
                    ]
                }
            }

        """
        url = '/rest/V1/MetricData'
        start_time = self._java_timestamp(timeutils.dt_to_timestamp(start))
        end_time = self._java_timestamp(timeutils.dt_to_timestamp(end))
        period = period_minute * 60
        dimensions = '%s=%s' % (dimension_key, dimension_value)

        query = urllib.urlencode({
            'projectId': self.project_id,
            'Namespace': self.namespace,
            'MetricName': metric_name,
            'Dimensions': dimensions,
            'Period': period,
            'StartTime': start_time,
            'EndTime': end_time,
            # 'Statistics',
            # 'Convertor',
            'AccessKey': self.access_key,
        })
        url = url + "?" + query
        LOG.debug("GET %s" % url)
        return self._request('GET', url)

    def post_metric(self, metric_name, metric_value,
                    dimension_key, dimension_value,
                    aggregation_dimension=None):
        """Send MetricData to collect server by POST request.

        :param metric_datas_json: monitoring data in json format
        """

        metric_data = {
            'metricName': metric_name,
            'dimensions': "%s=%s" % (dimension_key, dimension_value),
            'value': metric_value,
        }
        if aggregation_dimension:
            aggregates = []
            for key, value in aggregation_dimension.iteritems():
                aggregates.append('%s=%s' % (key, value))
            aggregation = ','.join(aggregates)
            metric_data['aggregationDimensions'] = aggregation

        #NOTE(gtt): metricDatas is a list
        metric_datas_json = json.dumps({'metricDatas': [metric_data]})
        params = urllib.urlencode({
                'ProjectId': self.project_id,
                'Namespace': self.namespace,
                'MetricDatasJson': metric_datas_json,
                'AccessKey': self.access_key,
                'Signature': self.generate_signature("/rest/V1/MetricData",
                                                    'POST',
                                                    metric_datas_json)
        })
        LOG.debug("POST to monitor: %s" % metric_datas_json)
        self.do_post("/rest/V1/MetricData", params)

    def post_alarm(self, alarm_type, alarm_time, alarm_content,
                alarm_content_summary, identifier):
        """Send alarm data to collect server by POST request.

        :param alarm_type: alarm type defined by service provider
        :param alarm_time: time stamp
        :param alarm_content: alarm content for email alarm
        :param alarm_content_summary: brief content for phone alarm
        :param identifier: instance name
        """
        params = urllib.urlencode(
            {'projectId': self.project_id,
             'namespace': self.namespace,
             'alarmType': alarm_type,
             'alarmTime': long(alarm_time),
             'alarmContent': alarm_content,
             'alarmContentSummary': alarm_content_summary,
             'identifier': identifier})
        self.do_post("/rest/private/alarm/platformAdminAlarm", params)

    def string_to_sign(self, request_uri, http_method, metric_datas_json):
        """Generate string_to_sign for signature."""
        canonicalized_headers = ''
        canonicalized_resources = 'AccessKey=%s&MetricDatasJson=%s' \
                                  '&Namespace=%s&ProjectId=%s' % \
                                  (self.access_key, metric_datas_json,
                                   self.namespace, self.project_id)

        string_to_sign = '%s\n%s\n%s\n%s\n' % \
                        (http_method, request_uri,
                        canonicalized_headers, canonicalized_resources)

        return string_to_sign

    def generate_signature(self,
                           request_uri,
                           http_method,
                           metric_datas_json):
        """Generate signature for authorization.

        Use hmac SHA-256 to calculate signature string and encode
        into base64.

        :returns: String of the signature
        """
        string_to_sign = self.string_to_sign(request_uri,
                                        http_method,
                                        metric_datas_json)
        hashed = hmac.new(str(self.access_secret), string_to_sign,
                          hashlib.sha256)
        s = hashed.digest()
        signature = s.encode('base64').rstrip()
        return signature

    def do_post(self, request_uri, param):
        return self._request('POST', request_uri, param)

    def _request(self, method, request_uri, param=None):
        method = method.upper()

        for i in xrange(5):
            try:
                conn = httplib.HTTPConnection(self.url, timeout=5)
                conn.request(method, request_uri, body=param,
                             headers=self.headers)
                response = conn.getresponse()
                if response.status != 200:
                    LOG.error("HTTP (status:%s):%s \ncontent:%s" %
                              (response.status, response.reason,
                               response.read().decode('utf8')))
                    continue  # retry
                return response.read()
            except Exception:
                time.sleep(i * 2)
            finally:
                if 'conn' in locals():
                    conn.close()


CLIENT = None


def get_client():
    """Get NCM client object, return None if config are not valid."""
    if not (CONF.ncm_host and CONF.ncm_port and
               CONF.ncm_access_key and CONF.ncm_secret_key):
        LOG.warn("'ncm_host', 'ncm_port', 'ncm_access_key', 'ncm_secret_key'"
                 " should be config. ")
        return None

    global CLIENT
    if not CLIENT:
        CLIENT = Monitor(CONF.ncm_host, CONF.ncm_port, CONF.ncm_project_id,
                         CONF.ncm_namespace, CONF.ncm_access_key,
                         CONF.ncm_secret_key)
    return CLIENT


def push_rpc_response_time(response_time, hostname, binary_name):
    client = get_client()
    if not client:
        LOG.warn("NCM Client is disabled, do not push metric.")
        return

    metric_name = 'rpc_response_time'
    metric_value = response_time
    dimension_name = 'service'
    dimension_value = '%s_%s' % (hostname, binary_name)
    aggregation_dimension = {'hostname': hostname, 'binary': binary_name}

    try:
        retryutils.retry_do(3, client.post_metric,
                            metric_name, metric_value, dimension_name,
                            dimension_value, aggregation_dimension)
    except Exception:
        LOG.exception("Push to NCM failed.")
    else:
        LOG.debug("Push to NCM successfully")
