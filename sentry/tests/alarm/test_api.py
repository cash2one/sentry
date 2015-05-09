import time

from sentry.alarm import api
from sentry.db.sqlalchemy import models
from sentry.openstack.common import timeutils
from sentry.tests import test


class AlarmJudgeTest(test.DBTestCase):
    def setUp(self):
        super(AlarmJudgeTest, self).setUp()
        self.judge = api.AlarmJudge()

    def test_can_fire_on_process(self):
        exception = models.ExcInfo(on_process=False)
        self.assertTrue(self.judge.can_fire(exception))

    def test_can_fire_in_shutup(self):
        exception = models.ExcInfo(
            on_process=False,
            shutup_start=timeutils.parse_local_isotime('2011-01-01'),
            shutup_end=timeutils.parse_local_isotime('9999-01-01')
        )
        self.assertFalse(self.judge.can_fire(exception))

    def test_can_fire_in_silent(self):
        exception = models.ExcInfo(on_process=False)
        self.assertTrue(self.judge.can_fire(exception))
        self.assertFalse(self.judge.can_fire(exception))
        self.assertFalse(self.judge.can_fire(exception))


class AlarmTimerTest(test.TestCase):

    def test_can_fire(self):
        self.timer = api.AlarmTimer(2)
        uuid = 'uuuuuuuid'
        uuid2 = 'uuuuuu2id'
        self.assertTrue(self.timer.can_fire(uuid))
        self.assertTrue(self.timer.can_fire(uuid2))

        self.assertFalse(self.timer.can_fire(uuid))
        self.assertFalse(self.timer.can_fire(uuid))
        self.assertFalse(self.timer.can_fire(uuid2))
        self.assertFalse(self.timer.can_fire(uuid2))

        time.sleep(3)
        self.assertTrue(self.timer.can_fire(uuid))
        self.assertTrue(self.timer.can_fire(uuid2))


class AlarmAPI(test.DBTestCase):
    def setUp(self):
        super(AlarmAPI, self).setUp()
        self.alarm = api.AlarmAPI()

    def test_alarm_service_broken(self):
        self.alarm.alarm_service_broken(
            'hostname1', 'nova-compute-x', '2014-03-03 00:00:22', 20
        )

    def test_alarm_service_recover(self):
        self.alarm.alarm_service_recover(
            'hostname2', 'nova-cmpute-y', '2014-02-02 22:11:33',
            '2013-04-04 22:33:44', 20,
        )
