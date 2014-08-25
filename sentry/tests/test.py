#
# Created on 2013-3-13
#
# @author: hzyangtk@corp.netease.com
#

import unittest
import stubout

from oslo.config import cfg


FLAGS = cfg.CONF


class TestCase(unittest.TestCase):
    """Test case base class for all unit tests."""

    def setUp(self):
        super(TestCase, self).setUp()
        self.stubs = stubout.StubOutForTesting()

    def tearDown(self):
        self.stubs.UnsetAll()

    def flags(self, **kw):
        """Override flag variables for a test."""
        for k, v in kw.iteritems():
            FLAGS.set_override(k, v)
