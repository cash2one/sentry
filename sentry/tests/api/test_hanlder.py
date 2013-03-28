#
# Created on 2013-3-27
#
# @author: hzyangtk@corp.netease.com
#

import webob

from sentry.api import base
from sentry.api import handler
from sentry.tests import test


class FakeRequest(object):

    def __init__(self, method='GET', path_info='/test',
                 remote_addr='1.1.1.1', params={}):
        self.method = method
        self.path_info = path_info
        self.remote_addr = remote_addr
        self.params = params


def fake_get_product_metric_list(req):
    return ['metric1']


def fake_get_platform_metric_list(req):
    return ['metric2']


def fake_get_product_alarm_event_list(req):
    return ['metric1']


def fake_get_platform_alarm_event_list(req):
    return ['metric2']


def fake_get_product_instance_list(req):
    return ['metric1']


def fake_get_platform_instance_list(req):
    return ['metric2']


class TestHandler(test.TestCase):

    def setUp(self):
        super(TestHandler, self).setUp()

    def tearDown(self):
        super(TestHandler, self).tearDown()

    def test_sentry_request_handler(self):
        handler_ins = handler.SentryRequestHandler()

        # get product metric list
        self.stubs.Set(base, "get_product_metric_list",
                       fake_get_product_metric_list)
        req = FakeRequest(path_info='/get-metric-list')
        result = handler_ins(req)
        self.assertEquals(['metric1'], result)

        # get platform metric list
        self.stubs.Set(base, "get_platform_metric_list",
                       fake_get_platform_metric_list)
        req = FakeRequest(path_info='/get-metric-list',
                          params={'IsPlatformManager': '1'})
        result = handler_ins(req)
        self.assertEquals(['metric2'], result)

        # get metric list exception raise
        req = FakeRequest(path_info='/get-metric-list',
                          params={'IsPlatformManager': 'other'})
        self.assertRaises(webob.exc.HTTPBadRequest, handler_ins, req)

        # get product alarm event list
        self.stubs.Set(base, "get_product_alarm_event_list",
                       fake_get_product_alarm_event_list)
        req = FakeRequest(path_info='/get-alarm-event-list')
        result = handler_ins(req)
        self.assertEquals(['metric1'], result)

        # get platform alarm event list
        self.stubs.Set(base, "get_platform_alarm_event_list",
                       fake_get_platform_alarm_event_list)
        req = FakeRequest(path_info='/get-alarm-event-list',
                          params={'IsPlatformManager': '1'})
        result = handler_ins(req)
        self.assertEquals(['metric2'], result)

        # get alarm event list exception raise
        req = FakeRequest(path_info='/get-alarm-event-list',
                          params={'IsPlatformManager': 'other'})
        self.assertRaises(webob.exc.HTTPBadRequest, handler_ins, req)

        # get product instance list
        self.stubs.Set(base, "get_product_instance_list",
                       fake_get_product_instance_list)
        req = FakeRequest(path_info='/get-instance-list')
        result = handler_ins(req)
        self.assertEquals(['metric1'], result)

        # get platform instance list
        self.stubs.Set(base, "get_platform_instance_list",
                       fake_get_platform_instance_list)
        req = FakeRequest(path_info='/get-instance-list',
                          params={'IsPlatformManager': '1'})
        result = handler_ins(req)
        self.assertEquals(['metric2'], result)

        # get instance list exception raise
        req = FakeRequest(path_info='/get-instance-list',
                          params={'IsPlatformManager': 'other'})
        self.assertRaises(webob.exc.HTTPBadRequest, handler_ins, req)

        # other request path
        req = FakeRequest(path_info='/other')
        self.assertRaises(webob.exc.HTTPBadRequest, handler_ins, req)
