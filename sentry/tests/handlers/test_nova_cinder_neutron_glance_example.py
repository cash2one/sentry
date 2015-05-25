from sentry.notification.handlers import nova
from sentry.notification.handlers import glance
from sentry.notification.handlers import cinder
from sentry.notification.handlers import neutron
from sentry.tests.handlers import _ExampleBaseTest


class NovaTest(_ExampleBaseTest):

    name = 'nova'

    def setUp(self):
        super(NovaTest, self).setUp()
        self.handler = nova.Handler()


class NeutronTest(_ExampleBaseTest):

    name = 'neutron'

    def setUp(self):
        super(NeutronTest, self).setUp()
        self.handler = neutron.Handler()


class CinderTest(_ExampleBaseTest):

    name = 'cinder'

    def setUp(self):
        super(CinderTest, self).setUp()
        self.handler = cinder.Handler()


class GlanceTest(_ExampleBaseTest):

    name = 'glance'

    def setUp(self):
        super(GlanceTest, self).setUp()
        self.handler = glance.Handler()
