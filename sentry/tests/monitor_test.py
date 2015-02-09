"""
Created on 2015-02-06

@author: hzliuchw
"""

from sentry.monitor import Monitor
import unittest


class DummyMonitor(Monitor):
    """init base info of monitor server"""
    def __init__(self, monitor_service_host, monitor_service_port,
                project_id, namespace, access_key, access_secret):
        super(DummyMonitor, self).__init__(monitor_service_host,
                                    monitor_service_port,
                                    project_id,
                                    namespace,
                                    access_key,
                                    access_secret)
        self.request_uri = None
        self.param = None

    def do_post(self, request_uri, param):
        self.request_uri = request_uri
        self.param = param


class MonitorTestCase(unittest.TestCase):
    def runTest(self):
        test_post_metric()
        test_post_alarm()

    def test_post_metric(self):
        dummy = DummyMonitor("127.0.0.1",
                             "1234",
                             "PROJECT_ID",
                             "TEST_NAMESPACE",
                             "monitor_access_key",
                             "monitor_access_secret")

        expected_url = "127.0.0.1:1234"
        expected_headers = {'Content-type':
                            'application/x-www-form-urlencoded'}
        expected_projected_id = "PROJECT_ID"
        expected_namespace = "TEST_NAMESPACE"
        self.assertEqual(dummy.url, expected_url)
        self.assertEqual(dummy.headers, expected_headers)
        self.assertEqual(dummy.project_id, expected_projected_id)
        self.assertEqual(dummy.namespace, expected_namespace)

        dummy.post_metric("value=99%")
        expected_uri = "/rest/V1/MetricData"
        expected_param = ('ProjectId=PROJECT_ID&AccessKey=monitor_access_key'
             '&Namespace=TEST_NAMESPACE&MetricDatasJson=value%3'
             'D99%25&Signature=8XHZJhnS9yxi%2BCp9if%2BtXrgJ1YUk'
             '%2B9wXW7Y4NQqjMtc%3D')

        self.assertEqual(dummy.request_uri, expected_uri)
        self.assertEqual(dummy.param, expected_param)

    def test_post_alarm(self):
        dummy = DummyMonitor("127.0.0.1",
                             "1234",
                             "PROJECT_ID",
                             "TEST_NAMESPACE",
                             "monitor_access_key",
                             "monitor_access_secret")

        expected_url = "127.0.0.1:1234"
        expected_headers = {'Content-type':
                            'application/x-www-form-urlencoded'}
        expected_projected_id = "PROJECT_ID"
        expected_namespace = "TEST_NAMESPACE"
        self.assertEqual(dummy.url, expected_url)
        self.assertEqual(dummy.headers, expected_headers)
        self.assertEqual(dummy.project_id, expected_projected_id)
        self.assertEqual(dummy.namespace, expected_namespace)

        dummy.post_alarm("ALARM_TYPE",
                          9999,
                         "JUST FOR TEST",
                         "TEST",
                         "SOMEIDENTIFIER")

        expected_uri = "/rest/private/alarm/platformAdminAlarm"
        expected_param = ('projectId=PROJECT_ID&namespace=TEST_NAMESPA'
                   'CE&alarmTime=9999&alarmContentSummary=TEST&a'
                   'larmContent=JUST+FOR+TEST&identifier=SOMEIDE'
                   'NTIFIER&alarmType=ALARM_TYPE')

        self.assertEqual(dummy.request_uri, expected_uri)
        self.assertEqual(dummy.param, expected_param)

if __name__ == '__main__':
    nittest.main()
