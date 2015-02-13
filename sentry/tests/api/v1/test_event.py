# -*-coding: utf8 -*-

from sentry.tests.api.v1 import base
from sentry.db import api as db_api
from sentry.db import models as base_models
from sentry.openstack.common import timeutils


class EventAPITests(base.V1AppTest):

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
        self._insert_event(user_name='1')
        self._insert_event(user_name='2')
        self._insert_event(user_name='3')

        resp = self.app.get('/events?limit=1')
        self.assertEqual(resp.json['pagination']['total_page'], 3)
        self.assertEqual(resp.json['pagination']['limit'], 1)
        self.assertEqual(resp.json['pagination']['current_page'], 1)

    def test_index_event_search_by_stuff(self):
        self._insert_event(user_name='1')
        self._insert_event(user_name='2')
        self._insert_event(user_name='3')

        resp = self.app.get('/events?user_name=1')
        self.assertEqual(resp.json['pagination']['total_page'], 1)
        self.assertEqual(resp.json['pagination']['limit'], 20)
        self.assertEqual(resp.json['pagination']['current_page'], 1)

        self.assertEqual(len(resp.json['events']), 1)
        self.assertEqual(resp.json['events'][0]['user_name'], '1')

    def test_index_event_sort_by(self):
        self._insert_event(user_name='1')
        self._insert_event(user_name='4')
        self._insert_event(user_name='9')
        self._insert_event(user_name='ab')

        resp = self.app.get('/events?sort=user_name')
        self.assertEqual(resp.json['pagination']['total_page'], 1)
        self.assertEqual(resp.json['pagination']['limit'], 20)
        self.assertEqual(resp.json['pagination']['current_page'], 1)

        self.assertEqual(resp.json['events'][0]['user_name'], '1')
        self.assertEqual(resp.json['events'][1]['user_name'], '4')
        self.assertEqual(resp.json['events'][2]['user_name'], '9')
        self.assertEqual(resp.json['events'][3]['user_name'], 'ab')

    def test_index_event_sort_by_desc(self):
        self._insert_event(user_name='1')
        self._insert_event(user_name='4')
        self._insert_event(user_name='9')
        self._insert_event(user_name='ab')

        resp = self.app.get('/events?sort=-user_name')
        self.assertEqual(resp.json['pagination']['total_page'], 1)
        self.assertEqual(resp.json['pagination']['limit'], 20)
        self.assertEqual(resp.json['pagination']['current_page'], 1)

        self.assertEqual(resp.json['events'][0]['user_name'], 'ab')
        self.assertEqual(resp.json['events'][1]['user_name'], '9')
        self.assertEqual(resp.json['events'][2]['user_name'], '4')
        self.assertEqual(resp.json['events'][3]['user_name'], '1')

    def test_index_event_schema(self):
        resp = self.app.get('/events/schema')

        self.assertTrue(resp.json['schema']['fields'])
        self.assertTrue(resp.json['schema']['searchable'])
        self.assertTrue(resp.json['schema']['sortable'])
