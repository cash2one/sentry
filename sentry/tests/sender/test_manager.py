#
# Created on 2013-3-26
#
# @author: hzyangtk@corp.netease.com
#

import copy

from sentry.file_cache import alarm_content as alarm_content_list
from sentry.sender import handler
from sentry.sender import http_sender
from sentry.sender import manager
from sentry.tests import test


TEMP_RESULT = None


fake_message = {
    'message_id': '00000000-0000-0000-0000-000000000001',
    'event_type': 'compute.instance.delete.end',
    'publisher_id': 'compute.host1',
    'priority': 'ERROR',
    'service': 'openstack',
    'timestamp': 'test_timestamp',
    '_context_project_id': '0000000000000000000000000000001',
    'payload': {'instance_id': '00000000-0000-0000-0000-000000000001',
                'tenant_id': '0000000000000000000000000000001',
                'project_id': '0000000000000000000000000000001',
                'display_name': 'instance-name',
                'uuid': '00000000-0000-0000-0000-000000000001',
                'request_spec': {'instance_properties': {
                                        'metadata': {'service': 'test'},
                                        'display_name': 'instance-name',
                                        'project_id':
                                            '0000000000000000000000000000001'
                                        },
                                 'instance_uuids': [
                                        '00000000-0000-0000-0000-000000000001']
                                 }
                },
    'alarm_owner': ['product_manager']
}

fake_alarm_summary_content = {
    'InstanceOffLine': 'test alarm summary content ',
    'InstanceError': 'test alarm summary content ',
    'NosError': 'test alarm summary content ',
    'NbsError': 'test alarm summary content ',
    'UnknownError': 'test alarm summary content '
}
fake_alarm_contents = {
    'InstanceOffLine': 'test alarm contents ',
    'InstanceError': 'test alarm contents ',
    'NosError': 'test alarm contents ',
    'NbsError': 'test alarm contents ',
    'UnknownError': 'test alarm contents '
}


def fake_data_formater(message):
    return {
        "projectId": "000000001",
        "namespace": message['service'],
        "alarmType": "test",
        "alarmTime": "test",
        "alarmContent": "test",
        "alarmContentSummary": "test",
        "identifier": "test"
    }


def fake_product_send_alarm(format_data):
    global TEMP_RESULT
    TEMP_RESULT = format_data
    TEMP_RESULT['owner'] = 'product'


def fake_platform_send_alarm(format_data):
    global TEMP_RESULT
    TEMP_RESULT = format_data
    TEMP_RESULT['owner'] = 'platform'


def fake_get_instance_ip(instance_uuid):
    return '1.1.1.1'


def fake_set_alarm_timestamp(message):
    return 'test_timestamp'


def fake_get_alarm_content():
    return {'alarm_summary_content': 'test',
            'alarm_content': 'test'}


def fake_is_instance_down(message, content):
    return True


def fake_format_instance_offline(message, summary, content):
    return {'test': 'test'}


class TestManager(test.TestCase):

    def setUp(self):
        super(TestManager, self).setUp()
        self.stubs.Set(handler, "get_instance_ip", fake_get_instance_ip)

    def tearDown(self):
        super(TestManager, self).setUp()
        global TEMP_RESULT
        TEMP_RESULT = None

    def test_send_alarm(self):
        self.flags(platform_project_id_list=['000000002'])
        self.stubs.Set(manager, "_data_formater", fake_data_formater)
        self.stubs.Set(http_sender, "product_send_alarm",
                       fake_product_send_alarm)
        self.stubs.Set(http_sender, "platform_send_alarm",
                       fake_platform_send_alarm)

        # when owner is product manager
        manager.send_alarm(fake_message)
        self.assertEquals('000000001', TEMP_RESULT.get('projectId'))
        self.assertEquals('product', TEMP_RESULT.get('owner'))

        # when owner is platform manager
        message = fake_message.copy()
        message['alarm_owner'] = ['platform_manager']
        manager.send_alarm(message)
        self.assertEquals('000000002', TEMP_RESULT.get('projectId'))
        self.assertEquals('platform', TEMP_RESULT.get('owner'))

        # when need not alarm
        message = fake_message.copy()
        message['service'] = 'RDS'
        result = manager.send_alarm(message)
        self.assertIsNone(result)

    def test_format_instance_offline(self):
        expect_result = {
            'projectId': '0000000000000000000000000000001',
            'namespace': 'openstack',
            'alarmType': 'InstanceOffLine',
            'alarmTime': 'test_timestamp',
            'alarmContent': 'test alarm contents name: instance-name, '
                            'uuid: 00000000-0000-0000-0000-000000000001'
                            ', ip: 1.1.1.1, '
                            'project id: 0000000000000000000000000000001',
            'alarmContentSummary': 'test alarm summary content instance-name:'
                                    '00000000-0000-0000-0000-000000000001',
            'identifier': 'instance-name:1.1.1.1'
        }
        result = manager._format_instance_offline(fake_message,
                            fake_alarm_summary_content, fake_alarm_contents)
        self.assertEquals(expect_result, result)

    def test_format_instance_error(self):
        expect_result = {
            'projectId': '0000000000000000000000000000001',
            'namespace': 'openstack',
            'alarmType': 'InstanceError',
            'alarmTime': 'test_timestamp',
            'alarmContent': 'test alarm contents name: instance-name, '
                            'uuid: 00000000-0000-0000-0000-000000000001'
                            ', ip: 1.1.1.1, '
                            'project id: 0000000000000000000000000000001'
                            ', old_state: '
                            ', old_task_state: '
                            ', state description: ',
            'alarmContentSummary': 'test alarm summary content instance-name:'
                                    '00000000-0000-0000-0000-000000000001',
            'identifier': 'instance-name:1.1.1.1'
        }
        result = manager._format_instance_error(fake_message,
                            fake_alarm_summary_content, fake_alarm_contents)
        self.assertEquals(expect_result, result)

    def test_format_nos_error(self):
        # when service is not glance
        expect_result = {
            'projectId': '0000000000000000000000000000001',
            'namespace': 'openstack',
            'alarmType': 'NosError',
            'alarmTime': 'test_timestamp',
            'alarmContent': 'test alarm contents compute.host1',
            'alarmContentSummary': 'test alarm summary content ',
            'identifier': 'compute.host1'
        }
        result = manager._format_nos_error(fake_message,
                            fake_alarm_summary_content, fake_alarm_contents)
        self.assertEquals(expect_result, result)

        # when service is from glance
        message = fake_message.copy()
        message['event_type'] = 'glance.create.start'
        message['payload'] = {}
        expect_result = {
            'projectId': '0000000000000000000000000000001',
            'namespace': 'openstack',
            'alarmType': 'NosError',
            'alarmTime': 'test_timestamp',
            'alarmContent': 'test alarm contents glance.compute.host1, '
                            'Detail: {}',
            'alarmContentSummary': 'test alarm summary content ',
            'identifier': 'glance.compute.host1'
        }
        result = manager._format_nos_error(message, fake_alarm_summary_content,
                                           fake_alarm_contents)
        self.assertEquals(expect_result, result)

    def test_format_nbs_error(self):
        expect_result = {
            'projectId': '0000000000000000000000000000001',
            'namespace': 'openstack',
            'alarmType': 'NbsError',
            'alarmTime': 'test_timestamp',
            'alarmContent': 'test alarm contents compute.host1',
            'alarmContentSummary': 'test alarm summary content ',
            'identifier': 'compute.host1'
        }
        result = manager._format_nbs_error(fake_message,
                            fake_alarm_summary_content, fake_alarm_contents)
        self.assertEquals(expect_result, result)

    def test_format_unknown_error(self):
        # message without request_spec
        message = copy.deepcopy(fake_message)
        message['payload']['metadata'] = [{'key': 'service', 'value': 'RDS'}]
        expect_result = {
            'projectId': '0000000000000000000000000000001',
            'namespace': 'RDS',
            'alarmType': 'UnknownError',
            'alarmTime': 'test_timestamp',
            'alarmContent': 'test alarm contents service name: compute, '
                            'event type: compute.instance.delete.end, '
                            'priority: ERROR',
            'alarmContentSummary': 'test alarm summary content ',
            'identifier': 'instance-name:1.1.1.1'
        }
        result = manager._format_unknown_error(message,
                            fake_alarm_summary_content, fake_alarm_contents)
        self.assertEquals(expect_result, result)

        # message with request_spec
        expect_result = {
            'projectId': '0000000000000000000000000000001',
            'namespace': 'test',
            'alarmType': 'UnknownError',
            'alarmTime': 'test_timestamp',
            'alarmContent': 'test alarm contents service name: compute, '
                            'event type: compute.instance.delete.end, '
                            'priority: ERROR',
            'alarmContentSummary': 'test alarm summary content ',
            'identifier': 'instance-name:1.1.1.1'
        }
        result = manager._format_unknown_error(fake_message,
                            fake_alarm_summary_content, fake_alarm_contents)
        self.assertEquals(expect_result, result)

    def test_data_formater(self):
        self.stubs.Set(handler, "set_alarm_timestamp",
                       fake_set_alarm_timestamp)
        self.stubs.Set(alarm_content_list, "get_alarm_content",
                       fake_get_alarm_content)
        self.stubs.Set(handler, "is_instance_down",
                       fake_is_instance_down)
        self.stubs.Set(manager, "_format_instance_offline",
                       fake_format_instance_offline)

        result = manager._data_formater(fake_message)
        self.assertEquals({'test': 'test'}, result)
