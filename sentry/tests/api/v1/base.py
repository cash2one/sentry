# -*-coding: utf8 -*-
import webtest

from sentry.tests import test
from sentry.api.v1.app import app as v1app


class V1AppTest(test.DBTestCase):
    def setUp(self):
        super(V1AppTest, self).setUp()
        self.app = webtest.TestApp(v1app)
