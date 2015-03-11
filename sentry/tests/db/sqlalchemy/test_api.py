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
            1, len(api._validate_sort_keys(models.Event, ['timestamp']))
        )

        self.assertEqual(
            2,
            len(api._validate_sort_keys(models.Event,
                                        ['timestamp', 'user_name']))
        )

    def test_validate_sort_key_passin_negtive(self):
        sort_cris = api._validate_sort_keys(
            models.Event, ['-timestamp', 'user_name'])

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

        timestr = kwargs.get('timestamp', '2013-01-21 08:51:29.179835')
        event.timestamp = timeutils.parse_isotime(timestr)
        event.raw_json = '{}'
        api.event_create(event)
        return event

    def test_create_event(self):
        # no exception raises
        self._insert_event(user_name='foo')

    def test_event_get_all_sort_by_user_name(self):
        event1 = self._insert_event(user_name='1')
        event2 = self._insert_event(user_name='2')
        result = api.event_get_all(sorts=['user_name'])

        self.assertEqual(2, result.count())
        self.assertEqual(event1.user_name, result.first().user_name)
        self.assertEqual(event2.user_name, result[1].user_name)

    def test_event_get_all_sort_by_user_name_desc(self):
        event1 = self._insert_event(user_name='1')
        event2 = self._insert_event(user_name='2')

        result = api.event_get_all(sorts=['-user_name'])

        self.assertEqual(2, result.count())
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
        result = api.event_get_all(sorts=['-user_name', 'request_id'])

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
        result = api.event_get_all(sorts=['-user_name', 'request_id'])

        self.assertEqual(2, result.count())
        self.assertEqual(event1.user_name, result[0].user_name,
                         "First result should be user_name2")
        self.assertEqual(event2.user_name, result[1].user_name,
                         "Second result should be user_name1")

        result = api.event_get_all(sorts=['-user_name', '-request_id'])

        self.assertEqual(event1.user_name, result[1].user_name,
                         "First result should be user_name2")
        self.assertEqual(event2.user_name, result[0].user_name,
                         "Second result should be user_name1")

    def test_event_get_all_search(self):
        event1 = self._insert_event(request_id='1', user_name='0')
        event2 = self._insert_event(request_id='2', user_name='0')

        result = api.event_get_all({'user_name': '0'},
                                          sorts=['request_id'])

        self.assertEqual(2, result.count())
        self.assertEqual(event1.request_id, result[0].request_id)
        self.assertEqual(event2.request_id, result[1].request_id)

    def test_event_get_all_search_no_result(self):
        event1 = self._insert_event(request_id='1', user_name='0')
        event2 = self._insert_event(request_id='2', user_name='0')

        result = api.event_get_all({'user_name': '2'})
        self.assertEqual(0, result.count())

    def test_event_get_all_search_one_result(self):
        event1 = self._insert_event(request_id='1', user_name='0')
        event2 = self._insert_event(request_id='2', user_name='0')

        result = api.event_get_all({'request_id': '1'})
        self.assertEqual(1, result.count())

    def test_event_get_all_between_start_and_end(self):
        self._insert_event(request_id='1', user_name='0',
                           timestamp='2013-01-01 00:00:00')
        self._insert_event(request_id='2', user_name='0',
                           timestamp='2013-02-02 00:00:00')
        result = api.event_get_all(start='2013-01-01 00:00:00')
        self.assertEqual(2, result.count())

        # plus 1 minute
        result = api.event_get_all(start='2013-01-01 00:00:01')
        self.assertEqual(1, result.count())

        result = api.event_get_all(start='2013-01-01 00:00:00',
                                   end='2013-01-02 00:00:00')
        self.assertEqual(1, result.count())

        result = api.event_get_all(start='2013-01-01 00:00:00',
                                   end='2013-02-02 00:00:01')
        self.assertEqual(2, result.count())

    def test_event_get_all_between_invalid_start(self):
        self._insert_event(request_id='1', user_name='0',
                                    timestamp='2013-01-01 00:00:00')
        result = api.event_get_all(start='2013-x1-x1 00:00:00')
        self.assertEqual(0, result.count())


class ExcInfoDBAPITests(test.DBTestCase):

    def test_create_exc_info(self):
        api.exc_info_detail_create(
           'host1', {}, binary='nova-api', exc_class='ValueError',
            exc_value='ValueError1', file_path='/usr/local/bin/test',
            func_name='testmethod', lineno=100,
            created_at=timeutils.parse_strtime("2013-03-03 01:03:04",
                                               '%Y-%m-%d %H:%M:%S')
        )

        query = api.exc_info_get_all()

        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().count, 1)

        # Create more
        api.exc_info_detail_create(
           'host1', {}, binary='nova-api', exc_class='ValueError',
            exc_value='ValueError1', file_path='/usr/local/bin/test',
            func_name='testmethod', lineno=100,
            created_at=timeutils.parse_strtime("2013-03-03 01:03:05",
                                               '%Y-%m-%d %H:%M:%S')
        )

        query = api.exc_info_get_all()

        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().count, 2)

        # Create another more
        api.exc_info_detail_create(
           'host1', {}, binary='nova-api', exc_class='OtherError',
            exc_value='ValueError1', file_path='/usr/local/bin/test',
            func_name='testmethod', lineno=100,
            created_at=timeutils.parse_strtime("2013-03-03 01:03:05",
                                               '%Y-%m-%d %H:%M:%S')
        )
        query = api.exc_info_get_all()

        self.assertEqual(query.count(), 2)

    def test_exc_info_get_all(self):
        api.exc_info_detail_create(
           'host1', {}, binary='nova-api', exc_class='ValueError',
            exc_value='ValueError1', file_path='/usr/local/bin/test',
            func_name='testmethod', lineno=100,
            created_at=timeutils.parse_strtime("2013-03-03 01:03:04",
                                               '%Y-%m-%d %H:%M:%S')
        )

        query = api.exc_info_get_all({'exc_class': 'ValueError'})
        self.assertEqual(query.count(), 1)

        query = api.exc_info_get_all({'exc_class': 'NoExisted'})
        self.assertEqual(query.count(), 0)

    def test_exc_info_get_all_boolean(self):
        exc = api.exc_info_detail_create(
            'host1', {}, binary='nova-api', exc_class='ValueError',
            exc_value='ValueError1', file_path='/usr/local/bin/test',
            func_name='testmethod', lineno=100,
            created_at=timeutils.parse_strtime("2013-03-03 01:03:04",
                                               '%Y-%m-%d %H:%M:%S')
        )
        api.exc_info_update(exc.uuid, {'on_process': True})
        # NOTE(gtt): Yes, we actually test boolean string.
        query = api.exc_info_get_all({'on_process': 'true'})
        self.assertEqual(query.count(), 1)

        query = api.exc_info_get_all({'on_process': 'false'})
        self.assertEqual(query.count(), 0)

    def test_exc_info_get_all_integer(self):
        for i in xrange(2):
            api.exc_info_detail_create(
                'host1', {}, binary='nova-api', exc_class='Error1',
                exc_value='ValueError1', file_path='/usr/local/bin/test',
                func_name='testmethod', lineno=100,
                created_at=timeutils.parse_strtime("2013-03-03 01:03:04",
                                                '%Y-%m-%d %H:%M:%S')
            )

        for i in xrange(1):
            api.exc_info_detail_create(
                'host1', {}, binary='nova-api', exc_class='Error2',
                exc_value='ValueError1', file_path='/usr/local/bin/test',
                func_name='testmethod', lineno=100,
                created_at=timeutils.parse_strtime("2013-03-03 01:03:04",
                                                '%Y-%m-%d %H:%M:%S')
            )

        query = api.exc_info_get_all({'count': '2'})
        self.assertEqual(query.count(), 1)

        query = api.exc_info_get_all({'count': 1})
        self.assertEqual(query.count(), 1)

    def test_exc_info_update(self):
        exc_detail = api.exc_info_detail_create(
           'host1', {}, binary='nova-api', exc_class='ValueError',
            exc_value='ValueError1', file_path='/usr/local/bin/test',
            func_name='testmethod', lineno=100,
            created_at=timeutils.parse_strtime("2013-03-03 01:03:04",
                                               '%Y-%m-%d %H:%M:%S')
        )
        api.exc_info_update(exc_detail.uuid, {'on_process': True})
        updated = api.exc_info_get_all({'uuid': exc_detail.uuid})[0]
        self.assertEqual(updated.on_process, True)

    def test_exc_info_detail_get_by_uuid_and_number_ok(self):
        exc_detail = api.exc_info_detail_create(
           'host1', {}, binary='nova-api', exc_class='ValueError',
            exc_value='ValueError1', file_path='/usr/local/bin/test',
            func_name='testmethod', lineno=100,
            created_at=timeutils.parse_strtime("2013-03-03 01:03:04",
                                               '%Y-%m-%d %H:%M:%S')
        )
        ret = api.exc_info_detail_get_by_uuid_and_number(exc_detail.uuid)
        self.assertEqual(ret.exc_class, exc_detail.exc_class)

    def test_exc_info_detail_get_by_uuid_not_found(self):
        ret = api.exc_info_detail_get_by_uuid_and_number('no-uuid')
        self.assertEqual(ret, None)

    def test_exc_info_detail_get_by_uuid_number_not_found(self):
        exc_detail = api.exc_info_detail_create(
            'host1', {}, binary='nova-api', exc_class='ValueError',
            exc_value='ValueError1', file_path='/usr/local/bin/test',
            func_name='testmethod', lineno=100,
            created_at=timeutils.parse_strtime("2013-03-03 01:03:04",
                                               '%Y-%m-%d %H:%M:%S')
        )
        ret = api.exc_info_detail_get_by_uuid_and_number(exc_detail.uuid, -1)
        self.assertEqual(ret, None)

        ret = api.exc_info_detail_get_by_uuid_and_number(exc_detail.uuid, 100)
        self.assertEqual(ret, None)
