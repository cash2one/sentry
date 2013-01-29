'''
Created on 2012-11-9

@author: Para
'''
import unittest
from sentry.common import utils
from sentry.controller.alarm_filter import AlarmFilter

class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testGet_alarm_level(self):
        TEST_CASE = ('INFO', 'WARN', 'ERROR', 'FATAL')
        self.assertEquals(utils.get_alarm_level(TEST_CASE[0]), ['INFO', 'WARN', 'ERROR', 'FATAL'], 'get alarm level error')
        self.assertEquals(utils.get_alarm_level(TEST_CASE[1]), ['WARN', 'ERROR', 'FATAL'], 'get alarm level error')
        self.assertEquals(utils.get_alarm_level(TEST_CASE[2]), ['ERROR', 'FATAL'], 'get alarm level error')
        self.assertEquals(utils.get_alarm_level(TEST_CASE[3]), ['FATAL'], 'get alarm level error')


    def testImport_object(self):
        driver = utils.import_object('sentry.controller.alarm_filter.AlarmFilter')
        print driver._accept_filter("test")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testGet_alarm_level']
    unittest.main()