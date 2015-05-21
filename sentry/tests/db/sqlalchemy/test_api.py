import datetime

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
        self._create_exception()

        query = api.exc_info_get_all()

        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().count, 1)

        # Create more
        self._create_exception()

        query = api.exc_info_get_all()

        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().count, 2)

        # Create another more
        self._create_exception(exc_class="OtherError")
        query = api.exc_info_get_all()

        self.assertEqual(query.count(), 2)

    def test_exc_info_get_all(self):
        self._create_exception(exc_class='ValueError')

        query = api.exc_info_get_all({'exc_class': 'ValueError'})
        self.assertEqual(query.count(), 1)

        query = api.exc_info_get_all({'exc_class': 'NoExisted'})
        self.assertEqual(query.count(), 0)

    def test_exc_info_get_all_default_return_not_on_process(self):
        error1 = self._create_exception(exc_class='Error1')
        api.exc_info_update(error1.uuid, {'on_process': True})
        error2 = self._create_exception(exc_class='Error2')

        query = api.exc_info_get_all()
        self.assertEqual(
            query.count(), 1,
            "Query should only return !on_process exceptions"
        )
        self.assertEqual(query.first().uuid, error2.uuid)

    def test_exc_info_get_all_boolean(self):
        exc = self._create_exception(exc_class='ValueError')
        api.exc_info_update(exc.uuid, {'on_process': True})
        # NOTE(gtt): Yes, we actually test boolean string.
        query = api.exc_info_get_all({'on_process': 'true'})
        self.assertEqual(query.count(), 1)

        query = api.exc_info_get_all({'on_process': 'false'})
        self.assertEqual(query.count(), 0)

    def test_exc_info_get_all_integer(self):
        for i in xrange(2):
            self._create_exception(exc_class='Error1')

        for i in xrange(1):
            self._create_exception(exc_class='Error2')

        query = api.exc_info_get_all({'count': '2'})
        self.assertEqual(query.count(), 1)

        query = api.exc_info_get_all({'count': 1})
        self.assertEqual(query.count(), 1)

    def test_exc_info_update(self):
        exc_detail = self._create_exception()
        api.exc_info_update(exc_detail.uuid, {'on_process': True})
        updated = api.exc_info_get_all({'on_process': True})[0]
        self.assertEqual(updated.on_process, True)

    def test_exc_info_detail_get_by_uuid_and_number_ok(self):
        exc_detail = self._create_exception()
        ret = api.exc_info_detail_get_by_uuid_and_number(exc_detail.uuid)
        self.assertEqual(ret.exc_class, exc_detail.exc_class)

    def test_exc_info_detail_get_by_uuid_not_found(self):
        ret = api.exc_info_detail_get_by_uuid_and_number('no-uuid')
        self.assertEqual(ret, None)

    def test_exc_info_detail_get_by_uuid_number_not_found(self):
        exc_detail = self._create_exception()
        ret = api.exc_info_detail_get_by_uuid_and_number(exc_detail.uuid, -1)
        self.assertEqual(ret, None)

        ret = api.exc_info_detail_get_by_uuid_and_number(exc_detail.uuid, 100)
        self.assertEqual(ret, None)


class InstanceNetworkStatusDBAPITests(test.DBTestCase):

    def _insert_instance_network_status(self, **kwargs):
        hostname = kwargs.get('hostname')
        uuid = kwargs.get('uuid')
        state = kwargs.get('state')
        api.instance_network_status_create_or_update(hostname,
                                                     uuid,
                                                     state)

        return {'hostname': hostname, 'uuid': uuid, 'state': state}

    def test_create_instance_network_status(self):
        # no exception raises
        self._insert_instance_network_status(hostname='fake-host',
                                             uuid='fake-uuid',
                                             state='normal')

    def test_instance_network_status_get_all_sort_by_host(self):
        ins1 = self._insert_instance_network_status(hostname='fake-host2',
                                                    uuid='fake-uuid2',
                                                    state='normal')
        ins2 = self._insert_instance_network_status(hostname='fake-host1',
                                                    uuid='fake-uuid1',
                                                    state='normal')
        result = api.instance_network_status_get_all(sorts=['hostname'])

        self.assertEqual(2, result.count())
        self.assertEqual(ins2['uuid'], result.first().uuid)
        self.assertEqual(ins1['uuid'], result[1].uuid)

    def test_instance_network_status_get_by_updated_at(self):
        ins1 = self._insert_instance_network_status(hostname='fake-host1',
                                                    uuid='fake-uuid2',
                                                    state='normal')
        time1 = timeutils.utcnow() + datetime.timedelta(seconds=60)
        time2 = timeutils.utcnow() - datetime.timedelta(seconds=60)

        res1 = api.instance_network_status_get_by_updated_at(time1)
        self.assertEqual(1, res1.count())

        res2 = api.instance_network_status_get_by_updated_at(time2)
        self.assertEqual(0, res2.count())


class PlatformStatusDBAPITests(test.DBTestCase):

    def _insert_platform_status(self, **kwargs):
        hostname = kwargs.get('hostname')
        item_name = kwargs.get('item_name')
        item_type = kwargs.get('item_type')
        state = kwargs.get('state')
        api.platform_status_create_or_update(hostname,
                                             item_type,
                                             item_name,
                                             state)

        return {'hostname': hostname, 'item_name': item_name,
                'item_type': item_type, 'state': state}

    def _insert_bulk_platform_status(self, **kwargs):
        hostname = kwargs.get('hostname')
        item_type = kwargs.get('item_type')
        items_state = kwargs.get('items_state')
        api.platform_status_bulk_create_or_update(hostname,
                                                  item_type,
                                                  items_state)

        return {'hostname': hostname, 'item_type': item_type,
                'items_state': items_state}

    def test_create_platform_status(self):
        # no exception raises
        self._insert_platform_status(hostname='fake-host',
                                     item_type='service',
                                     item_name='nova-compute',
                                     state='normal')

        services = {'nova-compute': 'normal', 'cinder-volume': 'normal'}
        self._insert_bulk_platform_status(hostname='fake-host2',
                                          item_type='service',
                                          items_state=services)
        result = api.platform_status_get_all(sorts=['hostname'])
        self.assertEqual(3, result.count())

    def test_update_platform_status(self):
        # no exception raises
        self._insert_platform_status(hostname='fake-host',
                                     item_type='service',
                                     item_name='nova-compute',
                                     state='normal')

        services = {'nova-compute': 'abnormal', 'cinder-volume': 'normal'}
        self._insert_bulk_platform_status(hostname='fake-host',
                                          item_type='service',
                                          items_state=services)
        result = api.platform_status_get_all(sorts=['hostname'])
        self.assertEqual(2, result.count())

    def test_platform_status_get_all_sort_by_host(self):
        ps1 = self._insert_platform_status(hostname='fake-host2',
                                           item_name='nova-compute',
                                           item_type='service',
                                           state='normal')
        ps2 = self._insert_platform_status(hostname='fake-host1',
                                           item_name='nova-compute',
                                           item_type='service',
                                           state='normal')
        result = api.platform_status_get_all(sorts=['hostname'])

        self.assertEqual(2, result.count())
        self.assertEqual(ps2['item_name'], result.first().item_name)
        self.assertEqual(ps1['item_type'], result[1].item_type)

    def test_platform_status_get_by_updated_at(self):
        ps1 = self._insert_platform_status(hostname='fake-host2',
                                           item_name='nova-compute',
                                           item_type='service',
                                           state='normal')
        time1 = timeutils.utcnow() + datetime.timedelta(seconds=60)
        time2 = timeutils.utcnow() - datetime.timedelta(seconds=60)

        res1 = api.platform_status_get_by_updated_at(time1)
        self.assertEqual(1, res1.count())

        res2 = api.platform_status_get_by_updated_at(time2)
        self.assertEqual(0, res2.count())
