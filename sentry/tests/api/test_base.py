#
# Created on 2013-3-27
#
# @author: hzyangtk@corp.netease.com
#

import webob

from sentry.api import base
from sentry.file_cache import setting_list
from sentry.openstack import client
from sentry.tests import test


def fake_get_setting_list():
    return {'product_metric_list': [{'test': 'test'}],
            'platform_NVSPlatform_metric_list': [{'test': 'test'}],
            'platform_host_metric_list': [{'test': 'test'}],
            'product_alarm_event_list': [{'test': 'test'}],
            'platform_alarm_event_list': [{'test': 'test'}]
            }


def fake_send_request_no_data(self, method, path, params, headers):
    return {}, {}


def fake_send_request_without_ip(self, method, path, params, headers):
    return {'servers': [{'addresses': {'private': []}}]}, {}


def fake_send_request_with_ip(self, method, path, params, headers):
    return {'servers': [{'addresses': {'private': [{'addr': '1.0.0.1'}]}}]}, {}


def fake_get_platform_host_list(tenant_id, token):
    return [{"id": "ubuntu", "screenName": "ubuntu"}]


def fake_get_platform_AZ_list(tenant_id, token):
    return [{"id": "nova", "screenName": "nova"}]


def fake_send_request_with_host(self, method, path, params, headers):
    return {'hosts': [{'host_name': 'host1'}]}, {}


def fake_send_request_without_host(self, method, path, params, headers):
    return {}, {}


def fake_send_request_with_AZ(self, method, path, params, headers):
    return {'availability_zones': [{'zoneState': 'available',
                                    'zoneName': 'nova'},
                                   {'zoneState': 'not available',
                                    'zoneName': 'fail'}]}, {}


def fake_send_request_without_AZ(self, method, path, params, headers):
    return {}, {}


class FakeRequest(object):

    def __init__(self, method='GET', path_info='/test',
                 remote_addr='1.1.1.1', params={}, headers={}):
        self.method = method
        self.path_info = path_info
        self.remote_addr = remote_addr
        self.params = params
        self.headers = headers


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

    def test_get_product_instance_list(self):
        # project id invalid
        req = FakeRequest(params={})
        self.assertRaises(webob.exc.HTTPBadRequest,
                          base.get_product_instance_list, req)

        # token is invalid
        req = FakeRequest(params={'ProjectId': '0001'})
        self.assertRaises(webob.exc.HTTPForbidden,
                          base.get_product_instance_list, req)

        # api no data return
        self.stubs.Set(client.NovaClient, "send_request",
                       fake_send_request_no_data)
        req = FakeRequest(params={'ProjectId': '0001'},
                          headers={'x-auth-token': '001'})
        expect_result = '[]'
        result = base.get_product_instance_list(req)
        self.assertEquals(expect_result, result)

        # api return data without ip
        self.stubs.Set(client.NovaClient, "send_request",
                       fake_send_request_without_ip)
        req = FakeRequest(params={'ProjectId': '0001'},
                          headers={'x-auth-token': '001'})
        expect_result = '[]'
        result = base.get_product_instance_list(req)
        self.assertEquals(expect_result, result)

        # api return data with ip
        self.stubs.Set(client.NovaClient, "send_request",
                       fake_send_request_with_ip)
        req = FakeRequest(params={'ProjectId': '0001'},
                          headers={'x-auth-token': '001'})
        expect_result = '["1.0.0.1"]'
        result = base.get_product_instance_list(req)
        self.assertEquals(expect_result, result)

    def test_get_platform_instance_list(self):
        # project id invalid
        req = FakeRequest(params={})
        self.assertRaises(webob.exc.HTTPBadRequest,
                          base.get_platform_instance_list, req)

        # token is invalid
        req = FakeRequest(params={'ProjectId': '0001'})
        self.assertRaises(webob.exc.HTTPForbidden,
                          base.get_platform_instance_list, req)

        # dimension name is host
        req = FakeRequest(params={'ProjectId': '0001',
                                  'DimensionName': 'host'},
                          headers={'x-auth-token': '001'})
        self.stubs.Set(base, "_get_platform_host_list",
                       fake_get_platform_host_list)
        expect_result = '[{"id": "ubuntu", "screenName": "ubuntu"}]'
        result = base.get_platform_instance_list(req)
        self.assertEquals(expect_result, result)

        # dimension name is Platform
        req = FakeRequest(params={'ProjectId': '0001',
                                  'DimensionName': 'Platform'},
                          headers={'x-auth-token': '001'})
        expect_result = '["NVSPlatform"]'
        result = base.get_platform_instance_list(req)
        self.assertEquals(expect_result, result)

        # dimension name is AZ
        req = FakeRequest(params={'ProjectId': '0001',
                                  'DimensionName': 'AZ'},
                          headers={'x-auth-token': '001'})
        self.stubs.Set(base, "_get_platform_AZ_list",
                       fake_get_platform_AZ_list)
        expect_result = '[{"id": "nova", "screenName": "nova"}]'
        result = base.get_platform_instance_list(req)
        self.assertEquals(expect_result, result)

    def test_get_platform_host_list(self):
        # Normal
        self.stubs.Set(client.NovaClient, "send_request",
                       fake_send_request_with_host)
        tenant_id = '0001'
        token = '001'
        expect_result = [{'id': 'host1', 'screenName': 'host1'}]
        result = base._get_platform_host_list(tenant_id, token)
        self.assertEquals(expect_result, result)

        # hosts is None
        self.stubs.Set(client.NovaClient, "send_request",
                       fake_send_request_without_host)
        self.assertRaises(webob.exc.HTTPNotFound,
                          base._get_platform_host_list, tenant_id, token)

    def test_get_platform_AZ_list(self):
        # Normal
        self.stubs.Set(client.NovaClient, "send_request",
                       fake_send_request_with_AZ)
        tenant_id = '0001'
        token = '001'
        expect_result = [{'id': 'nova', 'screenName': 'nova'}]
        result = base._get_platform_AZ_list(tenant_id, token)
        self.assertEquals(expect_result, result)

        # hosts is None
        self.stubs.Set(client.NovaClient, "send_request",
                       fake_send_request_without_AZ)
        self.assertRaises(webob.exc.HTTPNotFound,
                          base._get_platform_AZ_list, tenant_id, token)
