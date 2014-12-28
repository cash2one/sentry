#
# Created on 2013-3-26
#
# @author: hzyangtk@corp.netease.com
#

from sentry.controller.handlers import alarm as handler
from sentry.controller import helper as controller_helper
from sentry.openstack.common import importutils
from sentry.tests import test


fake_message = {
          'message_id': '00000000-0000-0000-0000-000000000001',
          'event_type': 'compute.create_instance',
          'publisher_id': 'compute.host1',
          'priority': 'ERROR',
          'payload': {'instance_id': 12, }
}


RESULT_SET = []


def fake_handle_before_alarm(message):
    pass


def fake_do_filter(self, flow_data):
    return {'alarm_owner': 'test'}


def fake_do_filter_exception(self, flow_data):
    raise Exception()


def fake_do_send_alarm(self, message):
    pass


class FakeFilter(object):

    def filter(self, flow_data):
        return {'alarm_owner': 'test'}


def fake_get_filter_drivers(self):
    if self._filter_drivers is None:
            self._filter_drivers = {}
    return [FakeFilter()]


def fake_add_filter_driver(self, filter_driver):
    self._filter_drivers = {'test': 'test_value'}


def fake_import_object(filter_driver):
    return FakeFilter()


class TestHandler(test.TestCase):

    def setUp(self):
        super(TestHandler, self).setUp()
        self.controller_handler = handler.Handler()

    def tearDown(self):
        super(TestHandler, self).tearDown()

    def test_handle_message(self):
        self.stubs.Set(controller_helper, "handle_before_alarm",
                       fake_handle_before_alarm)
        self.stubs.Set(handler.Handler, "_do_filter", fake_do_filter)
        self.stubs.Set(handler.Handler, "_do_send_alarm", fake_do_send_alarm)
        message = fake_message.copy()
        self.controller_handler.handle_message(message)
        self.assertEquals('test', message.get('alarm_owner'))

    def test_handle_message_exception(self):
        self.stubs.Set(controller_helper, "handle_before_alarm",
                       fake_handle_before_alarm)
        self.stubs.Set(handler.Handler, "_do_filter", fake_do_filter_exception)
        self.assertRaises(Exception, self.controller_handler, fake_message)

    def test_do_filter(self):
        self.stubs.Set(handler.Handler, "_get_filter_drivers",
                       fake_get_filter_drivers)
        flow_data = {}
        result = self.controller_handler._do_filter(flow_data)
        self.assertEquals('test', result.get('alarm_owner'))

    def test_get_filter_drivers(self):
        self.stubs.Set(handler.Handler, "_add_filter_driver",
                       fake_add_filter_driver)
        result = self.controller_handler._get_filter_drivers()
        self.assertEquals(['test_value'], result)

    def test_add_filter_driver(self):
        self.stubs.Set(handler.Handler, "_get_filter_drivers",
                       fake_get_filter_drivers)
        self.stubs.Set(importutils, "import_object",
                       fake_import_object)
        filter_driver = 'test_driver'
        self.controller_handler._add_filter_driver(filter_driver)
        self.assertIsInstance(
                self.controller_handler._filter_drivers.get('test_driver'),
                FakeFilter)
