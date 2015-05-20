from sentry.tests import test
from sentry.statsd import server


class TimeQueueTestCase(test.TestCase):

    def make_sample(self, value):
        return {
            'namespace': 'namespace',
            'dimension_name': 'dimension_name',
            'dimension_value': 'dimension_value',
            'metric_name': 'metric_name',
            'value': value,
            'type': 'ms',
            'sample_rate': '1',
            'tags': 'a:b'
        }

    def test_report_ok(self):
        # Test case copy from:
        # https://blog.pkhamre.com/understanding-statsd-and-graphite/
        queue = server.TimerQueue()
        queue.push_sample(self.make_sample(450))
        queue.push_sample(self.make_sample(120))
        queue.push_sample(self.make_sample(553))
        queue.push_sample(self.make_sample(994))
        queue.push_sample(self.make_sample(334))
        queue.push_sample(self.make_sample(844))
        queue.push_sample(self.make_sample(675))
        queue.push_sample(self.make_sample(496))

        ret = queue.report()
        self.assertEqual(ret['mean'], 558.25)
        self.assertEqual(ret['sum'], 4466)
        self.assertEqual(ret['count'], 8)
        self.assertEqual(ret['lower'], 120)
        self.assertEqual(ret['upper'], 994)

        self.assertEqual(ret['mean_90'], 496)
        self.assertEqual(ret['upper_90'], 844)
        self.assertEqual(ret['sum_90'], 3472)

    def test_no_data(self):
        queue = server.TimerQueue()
        # Make sure no raising
        queue.report()


class UDPDataTestCase(test.TestCase):

    def test_basic(self):
        sample1 = 'nvs.a.b.c:1|c'
        udp = server.UDPData(sample1)
        self.assertEqual(udp.namespace, 'nvs')
        self.assertEqual(udp.dimension_name, 'a')
        self.assertEqual(udp.dimension_value, 'b')
        self.assertEqual(udp.value, 1)
        self.assertEqual(udp.type_, 'c')

    def test_raises(self):
        sample = 'sdfs:2'
        self.assertRaises(ValueError, server.UDPData, sample)

        sample = 'sdfs:2|c'
        self.assertRaises(ValueError, server.UDPData, sample)

    def test_no_rate(self):
        sample = 'nvs.a.b.c:1|c|'
        udp = server.UDPData(sample)
        self.assertEqual(udp.namespace, 'nvs')
        self.assertEqual(udp.dimension_name, 'a')
        self.assertEqual(udp.dimension_value, 'b')
        self.assertEqual(udp.value, 1)
        self.assertEqual(udp.type_, 'c')
        self.assertEqual(udp.sample_rate, 1.0)
        self.assertEqual(udp.tags, None)

    def test_rate_ok(self):
        sample = 'nvs.a.b.c:1|c|@0.2'
        udp = server.UDPData(sample)
        self.assertEqual(udp.namespace, 'nvs')
        self.assertEqual(udp.dimension_name, 'a')
        self.assertEqual(udp.dimension_value, 'b')
        self.assertEqual(udp.value, 1)
        self.assertEqual(udp.type_, 'c')
        self.assertEqual(udp.tags, None)
        self.assertEqual(udp.sample_rate, 0.2)

    def test_rate_exceed(self):
        sample = 'nvs.a.b.c:1|c|@1.2'
        udp = server.UDPData(sample)
        self.assertEqual(udp.namespace, 'nvs')
        self.assertEqual(udp.dimension_name, 'a')
        self.assertEqual(udp.dimension_value, 'b')
        self.assertEqual(udp.value, 1)
        self.assertEqual(udp.type_, 'c')
        self.assertEqual(udp.tags, None)
        self.assertEqual(udp.sample_rate, 1.0)

    def test_with_tags(self):
        sample = 'nvs.a.b.c:1|c|@1.2|#a:c'
        udp = server.UDPData(sample)
        self.assertEqual(udp.namespace, 'nvs')
        self.assertEqual(udp.dimension_name, 'a')
        self.assertEqual(udp.dimension_value, 'b')
        self.assertEqual(udp.value, 1)
        self.assertEqual(udp.type_, 'c')
        self.assertEqual(udp.tags, 'a:c')
        self.assertEqual(udp.sample_rate, 1.0)

    def test_with_tag_no_rate(self):
        sample = 'nvs.a.b.c:1|c|#a:c'
        udp = server.UDPData(sample)
        self.assertEqual(udp.namespace, 'nvs')
        self.assertEqual(udp.dimension_name, 'a')
        self.assertEqual(udp.dimension_value, 'b')
        self.assertEqual(udp.value, 1)
        self.assertEqual(udp.type_, 'c')
        self.assertEqual(udp.tags, 'a:c')
        self.assertEqual(udp.sample_rate, 1.0)

    def test_with_tags2(self):
        sample = 'nvs.a.b.c:1|c|@1.2|#a:c,b:d'
        udp = server.UDPData(sample)
        self.assertEqual(udp.namespace, 'nvs')
        self.assertEqual(udp.dimension_name, 'a')
        self.assertEqual(udp.dimension_value, 'b')
        self.assertEqual(udp.value, 1)
        self.assertEqual(udp.type_, 'c')
        self.assertEqual(udp.tags, 'a:c,b:d')
        self.assertEqual(udp.sample_rate, 1.0)
