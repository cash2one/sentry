# -*-coding: utf8 -*-

from sentry.tests.api.v1 import base
from sentry.db import api as dbapi


class PlatformStatusAPITests(base.V1AppTest):

    def test_index_platform_status(self):
        ret = self.app.get('/platform_status')
        self.assertEqual(ret.status_code, 200)
