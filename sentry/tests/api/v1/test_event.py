# -*-coding: utf8 -*-

import webtest

from sentry.api.v1.app import app as v1app
from sentry.db import api as db_api
from sentry.db import models as base_models
from sentry.openstack.common import timeutils
from sentry.tests import test


class EventAPITests(test.DBTestCase):
    def setUp(self):
        super(EventAPITests, self).setUp()
        self.app = webtest.TestApp(v1app)

    def _insert_event(self, **kwargs):
        event = base_models.Event()

        for key, value in kwargs.iteritems():
            setattr(event, key, value)

        event.timestamp = timeutils.parse_isotime('2013-01-21 08:51:29.179835')
        event.raw_json = '{}'
        db_api.event_create(event)
        return event

    def test_index_no_events(self):
        resp = self.app.get('/events')

        self.assertEqual(resp.json['pagination']['total_page'], 0)
        self.assertEqual(resp.json['pagination']['limit'], 20)
        self.assertEqual(resp.json['pagination']['current_page'], 1)

        resp = self.app.get('/events?limit=1')

        self.assertEqual(resp.json['pagination']['total_page'], 0)
        self.assertEqual(resp.json['pagination']['limit'], 1)
        self.assertEqual(resp.json['pagination']['current_page'], 1)

    def test_index_events(self):
        self._insert_event(token='1')
        self._insert_event(token='2')
        self._insert_event(token='3')

        resp = self.app.get('/events?limit=1')
        self.assertEqual(resp.json['pagination']['total_page'], 3)
        self.assertEqual(resp.json['pagination']['limit'], 1)
        self.assertEqual(resp.json['pagination']['current_page'], 1)

    def test_index_event_search_by_stuff(self):
        self._insert_event(token='1')
        self._insert_event(token='2')
        self._insert_event(token='3')

        resp = self.app.get('/events?token=1')
        self.assertEqual(resp.json['pagination']['total_page'], 1)
        self.assertEqual(resp.json['pagination']['limit'], 20)
        self.assertEqual(resp.json['pagination']['current_page'], 1)

        self.assertEqual(len(resp.json['events']), 1)
        self.assertEqual(resp.json['events'][0]['token'], '1')

    def test_index_event_sort_by(self):
        self._insert_event(token='1')
        self._insert_event(token='4')
        self._insert_event(token='9')
        self._insert_event(token='ab')

        resp = self.app.get('/events?sort=token')
        self.assertEqual(resp.json['pagination']['total_page'], 1)
        self.assertEqual(resp.json['pagination']['limit'], 20)
        self.assertEqual(resp.json['pagination']['current_page'], 1)

        self.assertEqual(resp.json['events'][0]['token'], '1')
        self.assertEqual(resp.json['events'][1]['token'], '4')
        self.assertEqual(resp.json['events'][2]['token'], '9')
        self.assertEqual(resp.json['events'][3]['token'], 'ab')

    def test_index_event_sort_by_desc(self):
        self._insert_event(token='1')
        self._insert_event(token='4')
        self._insert_event(token='9')
        self._insert_event(token='ab')

        resp = self.app.get('/events?sort=-token')
        self.assertEqual(resp.json['pagination']['total_page'], 1)
        self.assertEqual(resp.json['pagination']['limit'], 20)
        self.assertEqual(resp.json['pagination']['current_page'], 1)

        self.assertEqual(resp.json['events'][0]['token'], 'ab')
        self.assertEqual(resp.json['events'][1]['token'], '9')
        self.assertEqual(resp.json['events'][2]['token'], '4')
        self.assertEqual(resp.json['events'][3]['token'], '1')

    def test_index_event_schema(self):
        resp = self.app.get('/events/schema')

        self.assertTrue(resp.json['schema']['fields'])
        self.assertTrue(resp.json['schema']['searchable'])
        self.assertTrue(resp.json['schema']['sortable'])
