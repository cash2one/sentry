import memcache

import sentry
from sentry.tests import test
from sentry.crons import platform_watcher
from sentry.openstack.common import timeutils


class PlatformWatcherManagerTest(test.TestCase):

    class MemcacheClient():
        def __init__(self, memcache_servers=[]):
            self.values = {'fake-host':
                            {'timestamp': '2015-05-15 08:01:30',
                            'uuids': ['fake-uuid1', 'fake-uuid2']},
                            'fake-uuid1_heart': '2015-05-15 08:14:41',
                            'fake-uuid12_heart': '2015-05-15 08:14:41'}

        def get(self, key):
            return self.values.get(key)

    def setUp(self):
        super(PlatformWatcherManagerTest, self).setUp()

    def test_get_all_service_status(self):
        result = {'fake-host1': {'services': {'nova-compute': 'abnormal'},
                                 'vms': {}, 'status': None},
                  'fake-host2': {'services': {'cinder-volume': 'abnormal'},
                                 'vms': {}, 'status': None}}

        def fake_db_service_status_get_all(**kwargs):
            class Service_status():
                def __init__(self, hostname, binary, state):
                    self.hostname = hostname
                    self.binary = binary
                    self.state = state

            class SqlServiceStatus():
                def all(self):
                    return [Service_status('fake-host1', 'nova-compute',
                                           'failed'),
                            Service_status('fake-host2', 'cinder-volume',
                                           'timeout')]
            return SqlServiceStatus()

        self.stubs.Set(sentry.db.api, 'service_status_get_all',
                       fake_db_service_status_get_all)
        pw = platform_watcher.PlatformWatcherManager()
        pw._get_all_service_status()
        self.assertEqual("%s" % result, "%s" % pw.status)

    def test_get_instance_list_by_host(self):
        result = ['fake-uuid1', 'fake-uuid2']

        self.stubs.Set(memcache, 'Client', self.MemcacheClient)
        pw = platform_watcher.PlatformWatcherManager()
        self.assertEqual(result, pw._get_instance_list_by_host('fake-host'))

    def test_get_instance_heartbeat_status(self):
        def fake_is_older_than(time1, interval):
            return False

        self.stubs.Set(memcache, 'Client', self.MemcacheClient)
        self.stubs.Set(timeutils, 'is_older_than', fake_is_older_than)
        pw = platform_watcher.PlatformWatcherManager()
        self.assertEqual('normal',
                         pw._get_instance_heartbeat_status('fake-uuid1'))

    def test_get_instance_network_status(self):
        def fake_instance_network_status_get_by_updated_at(*args, **kwargs):
            class SqlInstanceNetworkStatus():
                def __init__(fake_self, ins):
                    fake_self.ins = ins

                def all(fake_self):
                    return fake_self.ins

            if kwargs["search_dict"].get('uuid') == 'fake-uuid1':
                return SqlInstanceNetworkStatus([])
            elif kwargs["search_dict"].get('uuid') == 'fake-uuid2':
                return SqlInstanceNetworkStatus(['fake-inst_net_stat1',
                                                 'fake-inst-net-stat2'])

        self.stubs.Set(sentry.db.api,
                       'instance_network_status_get_by_updated_at',
                       fake_instance_network_status_get_by_updated_at)

        pw = platform_watcher.PlatformWatcherManager()
        self.assertEqual('normal',
                         pw._get_instance_network_status('fake-uuid1'))
        self.assertEqual('abnormal',
                         pw._get_instance_network_status('fake-uuid2'))

    def test_get_instance_status(self):
        def fake_get_instance_heartbeat_status(fake_self, uuid):
            if uuid == 'fake-uuid1':
                return 'normal'
            elif uuid == 'fake-uuid2':
                return 'normal'
            elif uuid == 'fake-uuid3':
                return 'abnormal'
            elif uuid == 'fake-uuid4':
                return 'abnormal'

        def fake_get_instance_network_status(fake_self, uuid):
            if uuid == 'fake-uuid1':
                return 'normal'
            elif uuid == 'fake-uuid2':
                return 'abnormal'
            elif uuid == 'fake-uuid3':
                return 'normal'
            elif uuid == 'fake-uuid4':
                return 'abnormal'

        self.stubs.Set(platform_watcher.PlatformWatcherManager,
                       '_get_instance_heartbeat_status',
                       fake_get_instance_heartbeat_status)
        self.stubs.Set(platform_watcher.PlatformWatcherManager,
                       '_get_instance_network_status',
                       fake_get_instance_network_status)
        pw = platform_watcher.PlatformWatcherManager()
        self.assertEqual('normal',
                         pw._get_instance_status('fake-uuid1'))
        self.assertEqual('network_abnormal',
                         pw._get_instance_status('fake-uuid2'))
        self.assertEqual('heartbeat_abnormal',
                         pw._get_instance_status('fake-uuid3'))
        self.assertEqual('heartbeat_network_abnormal',
                         pw._get_instance_status('fake-uuid4'))

    def test_update_platform_vms_status(self):
        result = {'fake-host1':
                  {'services': {'nova-compute': 'abnormal'},
                   'vms': {'fake-uuid1': 'normal',
                           'fake-uuid2': 'heartbeat_abnormal'},
                   'status': None},
                  'fake-host2':
                  {'services': {'cinder-volume': 'abnormal'},
                   'vms': {'fake-uuid3': 'network_abnormal',
                           'fake-uuid4': 'heartbeat_network_abnormal'},
                   'status': None}}

        def fake_get_instance_list_by_host(fake_self, host):
            if host == 'fake-host1':
                return ['fake-uuid1', 'fake-uuid2']
            elif host == 'fake-host2':
                return ['fake-uuid3', 'fake-uuid4']

        def fake_get_instance_status(fake_self, uuid):
            if uuid == 'fake-uuid1':
                return 'normal'
            elif uuid == 'fake-uuid2':
                return 'heartbeat_abnormal'
            elif uuid == 'fake-uuid3':
                return 'network_abnormal'
            elif uuid == 'fake-uuid4':
                return 'heartbeat_network_abnormal'

        def fake_db_service_status_get_all(**kwargs):
            class Service_status():
                def __init__(self, hostname, binary, state):
                    self.hostname = hostname
                    self.binary = binary
                    self.state = state

            class SqlServiceStatus():
                def all(self):
                    return [Service_status('fake-host1', 'nova-compute',
                                           'failed'),
                            Service_status('fake-host2', 'cinder-volume',
                                           'timeout')]
            return SqlServiceStatus()

        self.stubs.Set(sentry.db.api, 'service_status_get_all',
                       fake_db_service_status_get_all)
        self.stubs.Set(platform_watcher.PlatformWatcherManager,
                       '_get_instance_list_by_host',
                       fake_get_instance_list_by_host)
        self.stubs.Set(platform_watcher.PlatformWatcherManager,
                       '_get_instance_status',
                       fake_get_instance_status)
        pw = platform_watcher.PlatformWatcherManager()
        pw._get_all_service_status()
        pw._update_platform_vms_status()
        self.assertEqual("%s" % result, "%s" % pw.status)

    def test_update_platform_host_status(self):
        result = {'fake-host1':
                  {'services': {'nova-compute': 'abnormal'},
                   'vms': {'fake-uuid1': 'normal',
                           'fake-uuid2': 'normal'},
                   'status': 'service_abnormal'},
                  'fake-host2':
                  {'services': {'cinder-volume': 'abnormal'},
                   'vms': {'fake-uuid3': 'network_abnormal',
                           'fake-uuid4': 'heartbeat_network_abnormal'},
                   'status': 'node_abnormal'}}

        def fake_get_instance_list_by_host(fake_self, host):
            if host == 'fake-host1':
                return ['fake-uuid1', 'fake-uuid2']
            elif host == 'fake-host2':
                return ['fake-uuid3', 'fake-uuid4']

        def fake_get_instance_status(fake_self, uuid):
            if uuid == 'fake-uuid1':
                return 'normal'
            elif uuid == 'fake-uuid2':
                return 'normal'
            elif uuid == 'fake-uuid3':
                return 'network_abnormal'
            elif uuid == 'fake-uuid4':
                return 'heartbeat_network_abnormal'

        def fake_db_service_status_get_all(**kwargs):
            class Service_status():
                def __init__(self, hostname, binary, state):
                    self.hostname = hostname
                    self.binary = binary
                    self.state = state

            class SqlServiceStatus():
                def all(self):
                    return [Service_status('fake-host1', 'nova-compute',
                                           'failed'),
                            Service_status('fake-host2', 'cinder-volume',
                                           'timeout')]
            return SqlServiceStatus()

        self.stubs.Set(sentry.db.api, 'service_status_get_all',
                       fake_db_service_status_get_all)
        self.stubs.Set(platform_watcher.PlatformWatcherManager,
                       '_get_instance_list_by_host',
                       fake_get_instance_list_by_host)
        self.stubs.Set(platform_watcher.PlatformWatcherManager,
                       '_get_instance_status',
                       fake_get_instance_status)
        pw = platform_watcher.PlatformWatcherManager()
        pw._get_all_service_status()
        pw._update_platform_vms_status()
        pw._update_platform_host_status()
        self.assertEqual("%s" % result, "%s" % pw.status)
