from sentry.tests import test
from sentry.db.sqlalchemy import api
from sentry.db.sqlalchemy import models


class DBAPITestCase(test.TestCase):

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

    def test_validate_sort_key_passin_incorrectly(self):
        self.assertRaises(
            ValueError,
            api._validate_sort_keys, models.Event, ['foo', 'project_name']
        )
