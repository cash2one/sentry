# -*-coding: utf8 -*-

from sentry.tests.api.v1 import base
from sentry.db import api as dbapi
from sentry.openstack.common import timeutils


class ServiceAPITests(base.V1AppTest):

    def test_index_services(self):
        ret = self.app.get('/services')
        self.assertEqual(ret.status_code, 200)

    def test_index_services_schema(self):
        ret = self.app.get('/services/schema')
        self.assertEqual(ret.status_code, 200)

    def test_index_services_history(self):
        ret = self.app.get('/services/history')
        self.assertEqual(ret.status_code, 200)

    def test_index_services_history_schema(self):
        ret = self.app.get('/services/history/schema')
        self.assertEqual(ret.status_code, 200)

    def test_index_service_history_note(self):
        history = dbapi.service_history_create(
            'binary', 'hostname', timeutils.local_now(), timeutils.local_now(),
            100
        )
        ret = self.app.post_json(
            '/services/history/%s/note' % history.id,
            {'note': 'blablabla'},
        )
        self.assertEqual(ret.status_code, 200)
