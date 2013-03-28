#
# Created on 2013-3-26
#
# @author: hzyangtk@corp.netease.com
#

from sentry.common import http_communication
from sentry.controller import helper
from sentry.tests import test


TEMP_RESULT = None


fake_message = {
    'message_id': '00000000-0000-0000-0000-000000000001',
    'event_type': 'compute.instance.delete.end',
    'publisher_id': 'compute.host1',
    'priority': 'ERROR',
    'payload': {'instance_id': '00000000-0000-0000-0000-000000000001',
                'tenant_id': '0000000000000000000000000000001',
                'display_name': 'instance-name'}
}


def fake_notify_platform_stop_alarm(message):
    global TEMP_RESULT
    TEMP_RESULT = 'destroy'


def fake_notify_platform_binding(message):
    global TEMP_RESULT
    TEMP_RESULT = 'create'


class FakeResponse(object):

    def __init__(self):
        self.status = 200


def fake_send_request_to_server(self):
    return FakeResponse()


def fake_send_request_to_server_400(self):
    response = FakeResponse()
    response.status = 400
    return response


def fake_send_request_to_server_None(self):
    return None


class TestHelper(test.TestCase):

    def setUp(self):
        super(TestHelper, self).setUp()

    def tearDown(self):
        super(TestHelper, self).tearDown()
        global TEMP_RESULT
        TEMP_RESULT = None

    def test_handle_before_alarm(self):
        self.flags(enable_platform_stop_alarm=True)
        self.flags(enable_platform_binding=True)
        self.stubs.Set(helper, "_notify_platform_stop_alarm",
                       fake_notify_platform_stop_alarm)
        self.stubs.Set(helper, "_notify_platform_binding",
                       fake_notify_platform_binding)
        # when event type is destroy vm notification
        destroy_message = fake_message.copy()
        helper.handle_before_alarm(destroy_message)
        self.assertEquals('destroy', TEMP_RESULT)

        # when event type is create vm notification
        create_message = fake_message.copy()
        create_message['event_type'] = 'compute.instance.create.end'
        helper.handle_before_alarm(create_message)
        self.assertEquals('create', TEMP_RESULT)

    def test_notify_platform_stop_alarm(self):
        # when response status is 200
        self.stubs.Set(http_communication.HttpCommunication,
                       "send_request_to_server", fake_send_request_to_server)
        helper._notify_platform_stop_alarm(fake_message)

        # when response status is other code
        self.stubs.Set(http_communication.HttpCommunication,
                       "send_request_to_server",
                       fake_send_request_to_server_400)
        helper._notify_platform_stop_alarm(fake_message)

        # when response status is None
        self.stubs.Set(http_communication.HttpCommunication,
                       "send_request_to_server",
                       fake_send_request_to_server_None)
        helper._notify_platform_stop_alarm(fake_message)

    def test_notify_platform_binding(self):
        # when response status is 200
        self.stubs.Set(http_communication.HttpCommunication,
                       "send_request_to_server", fake_send_request_to_server)
        helper._notify_platform_binding(fake_message)

        # when response status is other code
        self.stubs.Set(http_communication.HttpCommunication,
                       "send_request_to_server",
                       fake_send_request_to_server_400)
        helper._notify_platform_binding(fake_message)

        # when response status is None
        self.stubs.Set(http_communication.HttpCommunication,
                       "send_request_to_server",
                       fake_send_request_to_server_None)
        helper._notify_platform_binding(fake_message)
