# -*-coding: utf8 -*-

from sentry.tests.api.v1 import base


class AlarmAPITest(base.V1AppTest):

    def test_index(self):
        ret = self.app.get('/alarms')
        self.assertEqual(ret.status_code, 200)

    def test_index_exception(self):
        ret = self.app.get('/alarms?type=exception')
        self.assertEqual(ret.status_code, 200)

    def test_action_ok(self):
        ret = self.app.post_json('/alarms/action',
                                 {'alarms': [], 'action': 'enable'})
        self.assertEqual(ret.status_code, 200)

    def test_action_no_action(self):
        ret = self.app.post('/alarms/action', expect_errors=True)
        self.assertEqual(ret.status_code, 400)

    def test_action_no_alarms(self):
        ret = self.app.post_json('/alarms/action',
                                 {'action': 'enable'}, expect_errors=True)
        self.assertEqual(ret.status_code, 400)

    def test_action_invalid_action(self):
        ret = self.app.post_json('/alarms/action',
                                 {'action': 'duang'}, expect_errors=True)
        self.assertEqual(ret.status_code, 400)

    def test_schema(self):
        ret = self.app.get('/alarms/schema')
        self.assertEqual(ret.status_code, 200)
