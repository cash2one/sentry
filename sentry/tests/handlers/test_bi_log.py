from sentry.tests import test
from sentry.bi import engine as bi_engine
from sentry.bi import case as bi_case


class BIAnalyzerTest(test.TestCase):

    def setUp(self):
        super(BIAnalyzerTest, self).setUp()
