#
# Created on 2013-3-26
#
# @author: hzyangtk@corp.netease.com
#

import os

from sentry.filter import alarm_filter
from sentry.tests import test


fake_flow_data = {
    'alarm_type': 'instance.create.start',
    'alarm_level': 'ERROR',
    'alarm_owner': []
}


def fake_reject_filter(flow_data):
    return flow_data


class TestAlarmFilter(test.TestCase):

    def setUp(self):
        super(TestAlarmFilter, self).setUp()
        DEFAULT_CONFIG_FILE = os.path.join(os.path.dirname(__file__),
                                           'alarm_filter.conf')
        self.flags(alarm_filter_config=DEFAULT_CONFIG_FILE)
        self.alarm_filter = alarm_filter.AlarmFilter()

    def tearDown(self):
        super(TestAlarmFilter, self).tearDown()

    def test_filter(self):
        self.alarm_filter.filters = [fake_reject_filter]
        result = self.alarm_filter.filter(fake_flow_data)
        expect_result = {
                            'alarm_type': 'instance.create.start',
                            'alarm_level': 'ERROR',
                            'alarm_owner': []
                        }
        self.assertEquals(expect_result, result)

    def test_reject_filter(self):
        # pass black list
        flow_data1 = fake_flow_data.copy()
        expect_result = {
                            'alarm_type': 'instance.create.start',
                            'alarm_level': 'ERROR',
                            'alarm_owner': []
                        }
        result = self.alarm_filter._reject_filter(flow_data1)
        self.assertEquals(expect_result, result)

        # reject by black list
        flow_data2 = fake_flow_data.copy()
        flow_data2['alarm_type'] = 'instance.delete.end'
        result = self.alarm_filter._reject_filter(flow_data2)
        self.assertIsNone(result)

        # alarm type not in reject rule level
        flow_data3 = fake_flow_data.copy()
        flow_data3['alarm_level'] = 'WARN'
        result = self.alarm_filter._reject_filter(flow_data3)
        self.assertIsNone(result)

    def test_accept_filter(self):
        # pass white list
        flow_data1 = fake_flow_data.copy()
        expect_result = {
                            'alarm_type': 'instance.create.start',
                            'alarm_level': 'ERROR',
                            'alarm_owner': []
                        }
        result = self.alarm_filter._accept_filter(flow_data1)
        self.assertEquals(expect_result, result)

        # filter by white list
        flow_data2 = fake_flow_data.copy()
        flow_data2['alarm_type'] = 'instance.delete.end'
        result = self.alarm_filter._accept_filter(flow_data2)
        self.assertIsNone(result)

        # alarm type not in accept rule level
        flow_data3 = fake_flow_data.copy()
        flow_data3['alarm_level'] = 'WARN'
        result = self.alarm_filter._accept_filter(flow_data2)
        self.assertIsNone(result)
