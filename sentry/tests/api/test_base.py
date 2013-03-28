#
# Created on 2013-3-27
#
# @author: hzyangtk@corp.netease.com
#

import webob

from sentry.api import base
from sentry.file_cache import setting_list
from sentry.tests import test


def fake_get_setting_list():
    return {'product_metric_list': [{'test': 'test'}],
            'platform_NVSPlatform_metric_list': [{'test': 'test'}],
            'platform_host_metric_list': [{'test': 'test'}],
            'product_alarm_event_list': [{'test': 'test'}],
            'platform_alarm_event_list': [{'test': 'test'}]
            }


class FakeRequest(object):

    def __init__(self, method='GET', path_info='/test',
                 remote_addr='1.1.1.1', params={}):
        self.method = method
        self.path_info = path_info
        self.remote_addr = remote_addr
        self.params = params


class TestBase(test.TestCase):

    def setUp(self):
        super(TestBase, self).setUp()
        self.stubs.Set(setting_list, "get_setting_list", fake_get_setting_list)

    def tearDown(self):
        super(TestBase, self).tearDown()

    def test_get_product_metric_list(self):
        expect_result = '[{"test": "test"}]'
        result = base.get_product_metric_list('')
        self.assertEquals(expect_result, result)

    def test_get_platform_metric_list(self):
        expect_result = '[{"test": "test"}]'
        req = FakeRequest(params={'DimensionName': 'Platform'})
        result = base.get_platform_metric_list(req)
        self.assertEquals(expect_result, result)

        req = FakeRequest(params={'DimensionName': 'host'})
        result = base.get_platform_metric_list(req)
        self.assertEquals(expect_result, result)

        req = FakeRequest(params={'DimensionName': 'other'})
        self.assertRaises(webob.exc.HTTPBadRequest,
                          base.get_platform_metric_list, req)

    def test_get_product_alarm_event_list(self):
        expect_result = '[{"test": "test"}]'
        result = base.get_product_alarm_event_list('')
        self.assertEquals(expect_result, result)

    def test_get_platform_alarm_event_list(self):
        expect_result = '[{"test": "test"}]'
        result = base.get_platform_alarm_event_list('')
        self.assertEquals(expect_result, result)
