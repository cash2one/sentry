
from sentry.db import api as dbapi
from sentry.notification import handlers
from sentry.notification.handlers import neutron_monitor
from sentry.tests.handlers import _ExampleBaseTest


class NeutronMonitorTest(_ExampleBaseTest):

    name = 'neutron_monitor'

    def _fake_db_save(*args, **kwargs):
        pass

    def _fake_db_get(*args, **kwargs):
        class Sql(object):
            def delete(fake_self):
                pass

        return Sql()

    def _stubs(self):
        super(NeutronMonitorTest, self)._stubs()
        self.stub.Set(dbapi, 'instance_network_status_create_or_update',
                      self._fake_db_save)
        self.stub.Set(dbapi, 'instance_network_status_get_all',
                      self._fake_db_get)

    def setUp(self):
        super(NeutronMonitorTest, self).setUp()
        self.handler = neutron_monitor.Handler()
