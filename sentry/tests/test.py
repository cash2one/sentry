# -*-coding: utf8 -*-

import unittest
import stubout

from oslo.config import cfg

from sentry.db.sqlalchemy import session
from sentry.db.sqlalchemy import models


CONF = cfg.CONF


class TestCase(unittest.TestCase):
    """Test case base class for all unit tests."""

    def setUp(self):
        super(TestCase, self).setUp()
        self.stubs = stubout.StubOutForTesting()

    def tearDown(self):
        self.stubs.UnsetAll()
        CONF.reset()

    def flags(self, **kw):
        """Override flag variables for a test."""
        for k, v in kw.iteritems():
            CONF.set_override(k, v)


class DBTestCase(TestCase):
    """With sqlite database setup"""

    def setUp(self):
        super(DBTestCase, self).setUp()
        self.flags(sql_connection='sqlite://')
        self.engine = session.get_engine()
        models.BASE.metadata.create_all(self.engine)

    def tearDown(self):
        models.BASE.metadata.drop_all(self.engine)
        super(DBTestCase, self).tearDown()
