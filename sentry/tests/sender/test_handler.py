#
# Created on 2013-3-27
#
# @author: hzyangtk@corp.netease.com
#

import time

from sentry.common import novaclient_helper
from sentry.sender import handler
from sentry.tests import fake_instance
from sentry.tests import test


fake_message = {
    'event_type': 'compute.test',
    'payload': {'state': 'error'}
}

fake_alarm_content = {
    'alarm_event_type': {'InstanceOffLine': 'compute.test',
                         'InstanceError': 'compute.test',
                         'NosError': 'compute.test',
                         'NbsError': 'compute.test'
                         }
}


def fake_get_instance_by_UUID(self, uuid):
    return fake_instance.FakeInstance(
                    addresses={'private': [{'addr': '1.1.1.1'}]})


def fake_get_instance_by_UUID_not_found(self, uuid):
    return fake_instance.FakeInstance()


class TestHandler(test.TestCase):

    def setUp(self):
        super(TestHandler, self).setUp()

    def tearDown(self):
        super(TestHandler, self).tearDown()

    def test_is_instance_down(self):
        result = handler.is_instance_down(fake_message, fake_alarm_content)
        self.assertTrue(result)

        # not instance down
        result = handler.is_instance_down(fake_message, {})
        self.assertFalse(result)

    def test_is_instance_state_error(self):
        result = handler.is_instance_state_error(fake_message,
                                                 fake_alarm_content)
        self.assertTrue(result)

        # not instance state error
        result = handler.is_instance_state_error(fake_message, {})
        self.assertFalse(result)

    def test_is_nos_connection_failure(self):
        result = handler.is_nos_connection_failure(fake_message,
                                                   fake_alarm_content)
        self.assertTrue(result)

        # not instance down
        result = handler.is_nos_connection_failure(fake_message, {})
        self.assertFalse(result)

    def test_is_nbs_connection_failure(self):
        result = handler.is_nbs_connection_failure(fake_message,
                                                   fake_alarm_content)
        self.assertTrue(result)

        # not instance down
        result = handler.is_nbs_connection_failure(fake_message, {})
        self.assertFalse(result)

    def test_get_instance_ip(self):
        self.stubs.Set(novaclient_helper.CallNovaClient,
                       "get_instance_by_UUID", fake_get_instance_by_UUID)
        result = handler.get_instance_ip('test_uuid')
        self.assertEquals('1.1.1.1', result)

        # get instance ip with exception happens
        self.stubs.Set(novaclient_helper.CallNovaClient,
                       "get_instance_by_UUID",
                       fake_get_instance_by_UUID_not_found)
        result = handler.get_instance_ip('test_uuid')
        self.assertEquals('-', result)

    def test_set_alarm_timestamp(self):
        # timestamp is not in message
        result = handler.set_alarm_timestamp(fake_message)
        self.assertGreaterEqual(long(time.time() * 1000), result['timestamp'])

        # timestamp is exist
        message = fake_message.copy()
        message['timestamp'] = '2012-03-27 15:51:11.123'
        result = handler.set_alarm_timestamp(message)
        self.assertGreater(long(time.time() * 1000), result['timestamp'])

        # timestamp is unicode format
        message['timestamp'] = u'2012-03-27 15:51:11.123'
        result = handler.set_alarm_timestamp(message)
        self.assertGreater(long(time.time() * 1000), result['timestamp'])

        # exception happens
        message['timestamp'] = 1
        result = handler.set_alarm_timestamp(message)
        self.assertGreaterEqual(long(time.time() * 1000), result['timestamp'])
