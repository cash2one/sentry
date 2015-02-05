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
        api._validate_search_dict(models.Event, {'user_name': 'hehe'})

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
        self._insert_event(user_name='foo')

    def test_event_get_all_sort_by_user_name(self):
        event1 = self._insert_event(user_name='1')
        event2 = self._insert_event(user_name='2')
        count, result = api.event_get_all(sorts=['user_name'])

        self.assertEqual(2, count)
        self.assertEqual(event1.user_name, result.first().user_name)
        self.assertEqual(event2.user_name, result[1].user_name)

    def test_event_get_all_sort_by_user_name_desc(self):
        event1 = self._insert_event(user_name='1')
        event2 = self._insert_event(user_name='2')

        count, result = api.event_get_all(sorts=['-user_name'])

        self.assertEqual(2, count)
        self.assertEqual(event2.user_name, result[0].user_name,
                         "First result should be user_name2")
        self.assertEqual(event1.user_name, result[1].user_name,
                         "Second result should be user_name1")

    def test_event_get_all_sort_by_multiple(self):
        event1 = self._insert_event(request_id='1', user_name='5')
        event2 = self._insert_event(request_id='2', user_name='4')

        # sort by desc user_name first, since two event have different
        # user_name.
        # so the result will not take request_id into consideration.
        count, result = api.event_get_all(sorts=['-user_name', 'request_id'])

        self.assertEqual(event1.user_name, result[0].user_name,
                         "First result should be user_name2")
        self.assertEqual(event2.user_name, result[1].user_name,
                         "Second result should be user_name1")

    def test_event_get_all_sort_by_multiple2(self):
        event1 = self._insert_event(request_id='1', user_name='0')
        event2 = self._insert_event(request_id='2', user_name='0')

        # sort by desc user_name first, since two event have the same user_name
        # id
        # so the result will be affected by request_id.
        count, result = api.event_get_all(sorts=['-user_name', 'request_id'])

        self.assertEqual(2, count)
        self.assertEqual(event1.user_name, result[0].user_name,
                         "First result should be user_name2")
        self.assertEqual(event2.user_name, result[1].user_name,
                         "Second result should be user_name1")

        count, result = api.event_get_all(sorts=['-user_name', '-request_id'])

        self.assertEqual(event1.user_name, result[1].user_name,
                         "First result should be user_name2")
        self.assertEqual(event2.user_name, result[0].user_name,
                         "Second result should be user_name1")

    def test_event_get_all_search(self):
        event1 = self._insert_event(request_id='1', user_name='0')
        event2 = self._insert_event(request_id='2', user_name='0')

        count, result = api.event_get_all({'user_name': '0'},
                                          sorts=['request_id'])

        self.assertEqual(2, count)
        self.assertEqual(event1.request_id, result[0].request_id)
        self.assertEqual(event2.request_id, result[1].request_id)

    def test_event_get_all_search_no_result(self):
        event1 = self._insert_event(request_id='1', user_name='0')
        event2 = self._insert_event(request_id='2', user_name='0')

        count, result = api.event_get_all({'user_name': '2'})
        self.assertEqual(0, count)

    def test_event_get_all_search_one_result(self):
        event1 = self._insert_event(request_id='1', user_name='0')
        event2 = self._insert_event(request_id='2', user_name='0')

        count, result = api.event_get_all({'request_id': '1'})
        self.assertEqual(1, count)
