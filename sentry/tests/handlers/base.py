import os
import sentry
import stubout
import unittest
import pprint

from sentry.openstack.common import jsonutils
from sentry.controller import handlers
from sentry.controller.handlers import nova
from sentry.controller.handlers import glance
from sentry.controller.handlers import cinder
from sentry.controller.handlers import neutron


class _ExampleBaseTest(unittest.TestCase):
    def setUp(self):
        self.unknows = []

        def no_save(*args, **kwargs):
            pass

        def save_unknown(x, msg):
            self.unknows.append(msg)

        self.stub = stubout.StubOutForTesting()
        self.handler = None
        self.stub.Set(handlers.PersistentHandler, 'save_event', no_save)
        self.stub.Set(handlers.PersistentHandler,
                      'save_unknown_event',
                      save_unknown)
        self.stub.Set(handlers.PersistentHandler, 'save_notification', no_save)

    def tearDown(self):
        self.stub.SmartUnsetAll()
        self.stub.UnsetAll()

    def test_examples(self):
        root_path = os.path.realpath(
            os.path.dirname(
                os.path.dirname(sentry.__file__)
            )
        )
        nova_path = os.path.join(root_path, 'doc', 'example', self.name)
        files = os.listdir(nova_path)

        for f in files:
            path = os.path.join(nova_path, f)
            with open(path) as filex:
                print "Test %s" % path
                content = filex.read()
                json = jsonutils.loads(content)
                self._try_process(json)

        pprint.pprint(self.unknows)

    def _try_process(self, json_msg):
        if not self.handler:
            raise Exception("Child class must setup self.handler first")

        return self.handler.handle_message(json_msg)


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
