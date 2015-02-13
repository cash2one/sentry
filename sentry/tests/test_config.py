import datetime

from sentry.tests import test
from sentry import config


class CacheDecorator(test.TestCase):

    @config.cache
    def _fake(self, key):
        return 'duang'

    def test_cache_not_cached(self):
        # Test with no cache
        self.cached = {}
        x = self._fake('he')
        self.assertEqual(x, 'duang')
        self.assertTrue(self.cached['he'])

        # Test with 12s old cache
        old = datetime.datetime.now() - datetime.timedelta(seconds=11)
        self.cached = {'he': ('duangduang', old)}
        x = self._fake('he')
        self.assertEqual(x, 'duang')

    def test_cache_does_cached(self):
        self.cached = {'he': ('duangduang', datetime.datetime.now())}
        x = self._fake('he')
        self.assertEqual(x, 'duangduang')


class ConfigTest(test.DBTestCase):
    def setUp(self):
        super(ConfigTest, self).setUp()
        self.config_engine = config.ConfigEngine()

    def test_register(self):
        cfg = config.Config('test', 'd-value')
        self.config_engine.register(cfg)
        self.assertTrue('test' in self.config_engine.keys())

    def test_get_config(self):
        cfg = config.Config('test', 'd-value')
        self.config_engine.register(cfg)
        self.assertEqual(self.config_engine.get_config('test'),
                         cfg.default_value)

    def test_items_with_secret(self):
        cfg = config.Config('test', 'd-value', secret=True)
        self.config_engine.register(cfg)
        ret = self.config_engine.items()
        self.assertEqual(ret['test'], '******')

    def test_iteritems(self):
        pass
