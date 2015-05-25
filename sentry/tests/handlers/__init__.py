"""sentry handlers"""
import os
import sentry
import stubout
import unittest
import pprint

from sentry.openstack.common import jsonutils
from sentry.notification import handlers
from sentry.notification.handlers import nova
from sentry.notification.handlers import glance
from sentry.notification.handlers import cinder
from sentry.notification.handlers import neutron
from sentry.notification.handlers import neutron_monitor


class _ExampleBaseTest(unittest.TestCase):

    name = 'test'

    def setUp(self):
        self.unknows = []
        self.logged = False

        def save_unknown(x, msg):
            self.unknows.append(msg)

        self.stub = stubout.StubOutForTesting()
        self.handler = None
        self._stubs()

    def _no_save(*args, **kwargs):
        pass

    def _stubs(self):
        self.stub.Set(handlers.MySQLHandler, 'save_event', self._no_save)

        # Make sure logging.exception() was not invoking
        handler_module = globals()[self.name]
        log = getattr(handler_module, 'LOG')
        self.stub.Set(log, 'exception', self._logging)

    def _logging(self, *args, **kwargs):
        self.logged = True

    def tearDown(self):
        self.stub.SmartUnsetAll()
        self.stub.UnsetAll()

    def test_examples(self):
        root_path = os.path.realpath(
            os.path.dirname(
                os.path.dirname(sentry.__file__)
            )
        )
        example_path = os.path.join(root_path, 'doc', 'example', self.name)
        files = os.listdir(example_path)

        for f in files:
            path = os.path.join(example_path, f)
            with open(path) as filex:
                print "Test %s" % path
                content = filex.read()
                json = jsonutils.loads(content)
                self._try_process(json)

        pprint.pprint(self.unknows)
        self.assertFalse(self.logged, 'Handler meets some exception')

    def _try_process(self, json_msg):
        if not self.handler:
            raise Exception("Child class must setup self.handler first")

        return self.handler.handle_message(json_msg)
