# -*-coding: utf8 -*-

from sentry.tests.api.v1 import base


class ConfigAPITests(base.V1AppTest):

    def test_index(self):
        ret = self.app.get('/configs')
        self.assertEqual(200, ret.status_code)

    def test_update(self):
        ret = self.app.post_json('/configs', {'duang': 'hehe'},
                                 expect_errors=True)
        self.assertEqual(400, ret.status_code)
