from sentry.tests import test
from sentry.common import retryutils


class RetryTestCase(test.TestCase):

    def test_retry_with_no_exception(self):
        called = {'number': 0}

        def hello():
            called['number'] += 1

        retryutils.retry_do(3, hello)
        self.assertEqual(called['number'], 1)

    def test_retry_in_exception(self):
        called = {'number': 0}

        def hello():
            called['number'] += 1
            raise Exception()

        self.assertRaises(Exception, retryutils.retry_do, 3, hello)
        self.assertEqual(called['number'], 4)
