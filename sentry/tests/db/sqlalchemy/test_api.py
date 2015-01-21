from sentry.tests import test
from sentry.db import models as base_models
from sentry.db.sqlalchemy import api
from sentry.db.sqlalchemy import models
from sentry.openstack.common import timeutils


class DBAPICommonTestCase(test.TestCase):

    def test_validate_search_dict_invalid(self):
        # no exception raised
        self.assertRaises(
            ValueError,
            api._validate_search_dict, models.Event, {'foo': 'bar'}
        )

    def test_validate_search_dict_correctly(self):
        # no exception raised
        api._validate_search_dict(models.Event, {})

        # no exception raised
        api._validate_search_dict(models.Event, {'id': 'hehe'})

    def test_validate_sort_key_passin_none(self):
        self.assertEqual(
            [], api._validate_sort_keys(models.Event, {})
        )
        self.assertEqual(
            [], api._validate_sort_keys(models.Event, None)
        )
        self.assertEqual(
            [], api._validate_sort_keys(models.Event, [])
        )

    def test_validate_sort_key_passin_correctly(self):
        self.assertEqual(
            1, len(api._validate_sort_keys(models.Event, ['id']))
        )

        self.assertEqual(
            2,
            len(api._validate_sort_keys(models.Event, ['id', 'project_name']))
        )

    def test_validate_sort_key_passin_negtive(self):
        sort_cris = api._validate_sort_keys(
            models.Event, ['-id', 'project_name'])

        self.assertTrue(
            str(sort_cris[0]).endswith('DESC')
        )

        self.assertTrue(
            str(sort_cris[1]).endswith('ASC')
        )

    def test_validate_sort_key_passin_incorrectly(self):
        self.assertRaises(
            ValueError,
            api._validate_sort_keys, models.Event, ['foo', 'project_name']
        )


class DBAPITests(test.DBTestCase):

    def _insert_event(self, **kwargs):
        event = base_models.Event()

        for key, value in kwargs.iteritems():
            setattr(event, key, value)

        event.timestamp = timeutils.parse_isotime('2013-01-21 08:51:29.179835')
        event.raw_json = '{}'
        api.event_create(event)
        return event

    def test_create_event(self):
        # no exception raises
        self._insert_event(token='foo')

    def test_event_get_all_sort_by_token(self):
        event1 = self._insert_event(token='1')
        event2 = self._insert_event(token='2')
        result = api.event_get_all(sorts=['token'])

        self.assertEqual(event1.token, result.first().token)
        self.assertEqual(event2.token, result[1].token)

    def test_event_get_all_sort_by_token_desc(self):
        event1 = self._insert_event(token='1')
        event2 = self._insert_event(token='2')

        result = api.event_get_all(sorts=['-token'])

        self.assertEqual(event2.token, result[0].token,
                         "First result should be token2")
        self.assertEqual(event1.token, result[1].token,
                         "Second result should be token1")

    def test_event_get_all_sort_by_multiple(self):
        event1 = self._insert_event(request_id='1', token='5')
        event2 = self._insert_event(request_id='2', token='4')

        # sort by desc token first, since two event have different token id
        # so the result will not take request_id into consideration.
        result = api.event_get_all(sorts=['-token', 'request_id'])

        self.assertEqual(event1.token, result[0].token,
                         "First result should be token2")
        self.assertEqual(event2.token, result[1].token,
                         "Second result should be token1")

    def test_event_get_all_sort_by_multiple2(self):
        event1 = self._insert_event(request_id='1', token='0')
        event2 = self._insert_event(request_id='2', token='0')

        # sort by desc token first, since two event have the same token id
        # so the result will be affected by request_id.
        result = api.event_get_all(sorts=['-token', 'request_id'])

        self.assertEqual(event1.token, result[0].token,
                         "First result should be token2")
        self.assertEqual(event2.token, result[1].token,
                         "Second result should be token1")

        result = api.event_get_all(sorts=['-token', '-request_id'])

        self.assertEqual(event1.token, result[1].token,
                         "First result should be token2")
        self.assertEqual(event2.token, result[0].token,
                         "Second result should be token1")

    def test_event_get_all_search(self):
        event1 = self._insert_event(request_id='1', token='0')
        event2 = self._insert_event(request_id='2', token='0')

        result = api.event_get_all({'token': '0'}, sorts=['request_id'])

        self.assertEqual(2, result.count())
        self.assertEqual(event1.request_id, result[0].request_id)
        self.assertEqual(event2.request_id, result[1].request_id)

    def test_event_get_all_search_no_result(self):
        event1 = self._insert_event(request_id='1', token='0')
        event2 = self._insert_event(request_id='2', token='0')

        result = api.event_get_all({'token': '2'})
        self.assertEqual(0, result.count())

    def test_event_get_all_search_one_result(self):
        event1 = self._insert_event(request_id='1', token='0')
        event2 = self._insert_event(request_id='2', token='0')

        result = api.event_get_all({'request_id': '1'})
        self.assertEqual(1, result.count())
