# -*-coding: utf8 -*-

from sentry.tests.api.v1 import base


class ExceptionAPITests(base.V1AppTest):

    def test_index(self):
        ret = self.app.get('/exceptions')
        self.assertEqual(ret.status_code, 200)

    def test_schema(self):
        ret = self.app.get('/exceptions')
        self.assertEqual(ret.status_code, 200)
