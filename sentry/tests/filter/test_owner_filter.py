#
# Created on 2013-3-26
#
# @author: hzyangtk@corp.netease.com
#

import copy
import os

from sentry.filter import owner_filter
from sentry.tests import test


fake_flow_data = {
    'alarm_type': 'instance.create.start',
    'alarm_level': 'ERROR',
    'alarm_owner': []
}


def fake_product_manager_blacklist_filter(flow_data):
    return flow_data


class TestOwnerFilter(test.TestCase):

    def setUp(self):
        super(TestOwnerFilter, self).setUp()
        DEFAULT_CONFIG_FILE = os.path.join(os.path.dirname(__file__),
                                           'owner_filter.conf')
        self.flags(owner_filter_config=DEFAULT_CONFIG_FILE)
        self.owner_filter = owner_filter.OwnerFilter()

    def tearDown(self):
        super(TestOwnerFilter, self).tearDown()

    def test_filter(self):
        self.owner_filter.filters = [fake_product_manager_blacklist_filter]
        result = self.owner_filter.filter(fake_flow_data)
        expect_result = {
                            'alarm_type': 'instance.create.start',
                            'alarm_level': 'ERROR',
                            'alarm_owner': []
                        }
        self.assertEquals(expect_result, result)

    def test_product_manager_blacklist_filter(self):
        # pass black list and add product to owner
        flow_data1 = copy.deepcopy(fake_flow_data)
        expect_result = {
                            'alarm_type': 'instance.create.start',
                            'alarm_level': 'ERROR',
                            'alarm_owner': ['product_manager']
                        }
        result = self.owner_filter._product_manager_blacklist_filter(
                                                            flow_data1)
        self.assertEquals(expect_result, result)

        # not pass and not add product to owner
        flow_data2 = copy.deepcopy(fake_flow_data)
        flow_data2['alarm_type'] = 'instance.delete.end'
        expect_result = {
                            'alarm_type': 'instance.delete.end',
                            'alarm_level': 'ERROR',
                            'alarm_owner': []
                        }
        result = self.owner_filter._product_manager_blacklist_filter(
                                                            flow_data2)
        self.assertEquals(expect_result, result)

    def test_platform_manager_blacklist_filter(self):
        # pass black list and add platform to owner
        flow_data1 = copy.deepcopy(fake_flow_data)
        expect_result = {
                            'alarm_type': 'instance.create.start',
                            'alarm_level': 'ERROR',
                            'alarm_owner': ['platform_manager']
                        }
        result = self.owner_filter._platform_manager_blacklist_filter(
                                                            flow_data1)
        self.assertEquals(expect_result, result)

        # not pass and not add platform to owner
        flow_data2 = copy.deepcopy(fake_flow_data)
        flow_data2['alarm_type'] = 'instance.delete.end'
        expect_result = {
                            'alarm_type': 'instance.delete.end',
                            'alarm_level': 'ERROR',
                            'alarm_owner': []
                        }
        result = self.owner_filter._platform_manager_blacklist_filter(
                                                            flow_data2)
        self.assertEquals(expect_result, result)

    def test_product_manager_whitelist_filter(self):
        # pass white list and add product to owner
        flow_data1 = copy.deepcopy(fake_flow_data)
        expect_result = {
                            'alarm_type': 'instance.create.start',
                            'alarm_level': 'ERROR',
                            'alarm_owner': ['product_manager']
                        }
        result = self.owner_filter._product_manager_whitelist_filter(
                                                            flow_data1)
        self.assertEquals(expect_result, result)

        # not pass and not add product to owner
        flow_data2 = copy.deepcopy(fake_flow_data)
        flow_data2['alarm_type'] = 'instance.delete.end'
        expect_result = {
                            'alarm_type': 'instance.delete.end',
                            'alarm_level': 'ERROR',
                            'alarm_owner': []
                        }
        result = self.owner_filter._product_manager_whitelist_filter(
                                                            flow_data2)
        self.assertEquals(expect_result, result)

    def test_platform_manager_whitelist_filter(self):
        # pass white list and add platform to owner
        flow_data1 = copy.deepcopy(fake_flow_data)
        expect_result = {
                            'alarm_type': 'instance.create.start',
                            'alarm_level': 'ERROR',
                            'alarm_owner': ['platform_manager']
                        }
        result = self.owner_filter._platform_manager_whitelist_filter(
                                                            flow_data1)
        self.assertEquals(expect_result, result)

        # not pass and not add platform to owner
        flow_data2 = copy.deepcopy(fake_flow_data)
        flow_data2['alarm_type'] = 'instance.delete.end'
        expect_result = {
                            'alarm_type': 'instance.delete.end',
                            'alarm_level': 'ERROR',
                            'alarm_owner': []
                        }
        result = self.owner_filter._platform_manager_whitelist_filter(
                                                            flow_data2)
        self.assertEquals(expect_result, result)
