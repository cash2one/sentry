"""
Created on 2015-02-10

@author: hzliuchw
"""

import httplib
import hmac
import urllib
import hashlib

from sentry.openstack.common import log as logging

LOG = logging.getLogger(__name__)


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

    def post_metric(self, metric_datas_json):
        """Send MetricData to collect server by POST request.

        :param metric_datas_json: monitoring data in json format
        """
        params = urllib.urlencode({
                'ProjectId': self.project_id,
                'Namespace': self.namespace,
                'MetricDatasJson': metric_datas_json,
                'AccessKey': self.access_key,
                'Signature': self.generate_signature("/rest/V1/MetricData",
                                                    'POST',
                                                    metric_datas_json)
        })
        LOG.debug(_("post to monitor: %s") % metric_datas_json)
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
        try:
            conn = httplib.HTTPConnection(self.url, timeout=5)
            conn.request('POST', request_uri, body=param, headers=self.headers)
            response = conn.getresponse()
            if response.status != 200:
                LOG.error(_("send alarm error: (status:%s):%s \ncontent:%s" %
                           (response.status, response.reason,
                            response.read().decode('utf8'))))
            else:
                LOG.debug(_("do_post success request_uri:5s param:%s"),
                            (rarequest_uri, param))
        except Exception as e:
            LOG.error(_("do_post error with expetion: %s" % e))
        finally:
            if 'conn' in locals():
                conn.close()
