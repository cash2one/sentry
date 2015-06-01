"""
A python implemented StatsD.

Expression:

ns.dimension_name.dimension_value.name:value|type|@sample_rate|#tag1:value,tag2

`ns` should be a String that specified the namespace.
`dimension_name` should be String specified the dimension name of the metric.
`dimension_value` should be a String specified the dimension value of the
metric.
`name` should be a String with no colons, bars or @ characters.
`value` should be a number
`type` should be c for Counter, g for Gauge, h for Histogram, ms for Timer or s
for Set. Full explanation of type
[here](https://github.com/etsy/statsd/blob/master/docs/metric_types.md).
`sample rate` is optional and should be a float between 0 and 1 inclusive.
`tags` are optional, and should be a comma seperated list of tags. colons are
used for key value tags. The first item of tags will be dimension, the other of
tags will be aggregation_dimension.
"""

import time
import socket
import logging as ori_logging
import sys

from oslo.config import cfg
import eventlet

from sentry.common import config
from sentry.openstack.common import log as logging
from sentry.statsd import backend_ncm

CONF = cfg.CONF
stats_opts = [
    cfg.StrOpt("bind_host", default="127.0.0.1",
            help="The host of statsd listens on."),
    cfg.IntOpt("bind_port", default=8125,
            help="The port os statsd listens on."),
    cfg.IntOpt('udp_buffer', default=8192,
            help="The default buffer size each time receive from UDP."),
    cfg.IntOpt("pool_size", default=3000,
            help="The cocurrency to process the UDP request. Default 3000"),
    cfg.IntOpt("flush_interval", default=60,
            help="The interval to send metric to NCM in seconds"),

]
CONF.register_opts(stats_opts, 'statsd')

LOG = logging.getLogger(__name__)


class MetricQueue(object):
    """The basic class for all types.

    Subclass should implement report(), and override push_sample() if need.
    """

    def __init__(self):
        self.tags = {}
        self.samples = []

        self.namespace = None
        self.dimension_name = None
        self.dimension_value = None
        self.metric_name = None

    def _clone_basic(self, sample):
        self.namespace = sample['namespace']
        self.dimension_name = sample['dimension_name']
        self.dimension_value = sample['dimension_value']
        self.metric_name = sample['metric_name']

    def _process_tag(self, tag_str):
        if tag_str:
            tags = tag_str.split(',')
            for tag in tags:
                try:
                    key, value = tag.split(':', 1)
                    self.tags[key] = value
                except ValueError:
                    LOG.warn("malformed tag: %s, found no ':' in here." % tag)

    def push_sample(self, sample):
        self._clone_basic(sample)
        self._process_tag(sample['tags'])

        try:
            value = float(sample['value'])
        except ValueError:
            value = 0

        self.samples.append(value)

    def report(self):
        raise NotImplementedError("Subclass should override report()")

    def clear(self):
        del self.samples[:]
        self.tags.clear()

    def to_dict(self):
        return {
            'namespace': self.namespace,
            'dimension_name': self.dimension_name,
            'dimension_value': self.dimension_value,
            'metric_name': self.metric_name,
            'tags': self.tags,
        }


class TimerQueue(MetricQueue):
    """The aggregator for type 'ms'."""

    default_percentiles = 0.9

    @staticmethod
    def split_sample(items, percentage=0.5):
        """Caller should make sure `items` is ordered from low to high.
        """
        index = int(round(len(items) * percentage))
        try:
            return items[:index]
        except IndexError:
            return []

    @staticmethod
    def average(items):
        try:
            ret = sum(items) / len(items)
        except ZeroDivisionError:
            ret = 0

        return ret

    def report(self):
        ordered_sample = sorted(self.samples)

        if ordered_sample:
            upper = ordered_sample[-1]
            lower = ordered_sample[0]
            count = len(ordered_sample)
            sum_all = sum(ordered_sample)
            mean = self.average(ordered_sample)
        else:
            upper = 0
            lower = 0
            count = 0
            sum_all = 0
            mean = 0

        sample_90 = self.split_sample(ordered_sample, self.default_percentiles)

        if sample_90:
            mean_90 = self.average(sample_90)
            upper_90 = sample_90[-1]
            sum_90 = sum(sample_90)
        else:
            mean_90 = 0
            upper_90 = 0
            sum_90 = 0

        return {
            'mean_90': mean_90,
            'upper_90': upper_90,
            'sum_90': sum_90,
            'upper': upper,
            'lower': lower,
            'count': count,
            'sum': sum_all,
            'mean': mean,
        }

    def push_sample(self, sample):
        super(TimerQueue, self).push_sample(sample)


class CounterQueue(MetricQueue):
    """The aggregator for type 'c'."""

    def push_sample(self, sample):
        rate = sample.sample_rate
        if rate:
            try:
                new_value = float(rate) * sample.value
                sample.value = new_value
            except TypeError as ex:
                LOG.warn(ex)
        super(CounterQueue, self).push_sample(sample)

    def report(self):
        sum_value = sum(self.samples)
        return sum_value


class UDPData(object):
    """The model represent a UDP package."""

    DEFAULT_RATE = 1.0

    def __init__(self, data):
        """Try best to parse UDP data, raises ValueError only core
        information is missing.

        The schema:
        ns.dimen_name.dimen_v.name:value|type|@sample_rate|#tag1:value,tag2
        """
        self.raw_data = data
        self._parse_data()
        self._parse_body()
        self._parse_key()

    def _parse_data(self):
        data = self.raw_data
        tokens = data.split('|')
        token_length = len(tokens)

        if token_length < 2 or token_length > 4:
            msg = ("malformed metric: <%s>" % (data))
            raise ValueError(msg)

        if token_length == 2:
            body, type_ = tokens
            sample_rate = self.DEFAULT_RATE
            tags = None

        elif token_length == 3:
            body, type_, other = tokens
            if self._is_sample_rate(other):
                sample_rate = other
                tags = None
            elif self._is_tags(other):
                sample_rate = None
                tags = other
            else:
                sample_rate = None
                tags = None

        else:  # token_length == 4
            body, type_, sample_rate, tags = tokens

        self.body = body
        self.type_ = type_
        self.sample_rate = self._clean_sample_rate(sample_rate)
        # string
        self.tags = self._clean_tags(tags)

    @staticmethod
    def _is_sample_rate(token):
        return token.strip().startswith('@')

    @staticmethod
    def _is_tags(token):
        return token.strip().startswith('#')

    def _parse_body(self):
        """Parse `ns.dimen_name.dimen_v.name:value`"""
        body = self.body
        tokens = body.split(':')

        if len(tokens) != 2:
            msg = 'body %s should contains `:`' % body
            raise ValueError(msg)

        key, value = tokens
        self.key = key
        self.value = float(value)

    def _parse_key(self):
        """Parse 'ns.dimen_name.dimen_v.name'"""
        tokens = self.key.split('.')

        if len(tokens) != 4:
            msg = "malformed key: %s" % self.key
            raise ValueError(msg)

        namespace, dimension_name, dimension_value, metric_name = tokens
        self.namespace = namespace
        self.dimension_name = dimension_name
        self.dimension_value = dimension_value
        self.metric_name = metric_name

    def _clean_sample_rate(self, sample_rate):
        """Validation and cleanup."""
        if isinstance(sample_rate, basestring):
            if sample_rate.startswith('@'):
                sample_rate = sample_rate.replace('@', '')
            else:
                LOG.warn("sample_rate should starts with @: %s" % sample_rate)
                sample_rate = self.DEFAULT_RATE

        if sample_rate is None:
            sample_rate = self.DEFAULT_RATE

        try:
            sample_rate = float(sample_rate)
        except ValueError:
            sample_rate = self.DEFAULT_RATE

        if sample_rate < 0 or sample_rate > 1:
            LOG.warn("sample_rate: %f should be in [0, 1]" % sample_rate)
            sample_rate = self.DEFAULT_RATE

        return sample_rate

    def _clean_tags(self, tags):
        if tags:
            if tags.startswith('#'):
                tags = tags.replace('#', '')
            else:
                LOG.warn("Tags should startswith #: %s" % tags)
                tags = None

        return tags

    def __getitem__(self, key):
        return getattr(self, key)


class StatsServer(object):
    """The Stats python implement"""

    def __init__(self):
        # Key: ns.dimen_name.dimen_value.name
        # Value: MetricQueue
        self.counter_samples = {}
        self.timer_samples = {}

        # TODO: when we want to add more backends, please
        # using auto loading mechanism
        self.backend = backend_ncm.NCMBackend()

    def process(self, data):
        udp = data.strip()
        try:
            metric = UDPData(udp)

            if metric.type_ == 'ms':
                queue = self.timer_samples.setdefault(metric.key,
                                                      TimerQueue())
                queue.push_sample(metric)

            elif metric.type_ == 'c':
                queue = self.counter_samples.setdefault(metric.key,
                                                        CounterQueue())
                queue.push_sample(metric)

            else:
                LOG.warn("Encountered unknown metric type in <%s>" %
                         (metric.type_))
        except Exception as ex:
            LOG.exception(ex)

    def _do_report(self, queue_obj):
        for sample in queue_obj.values():
            try:
                values = sample.report()
                metric_info = sample.to_dict()
                # NOTE(gtt): since values and metric_info was new object
                # not reference to sample, we can clear sample before
                # sending metric. And this make greenlet switching in
                # backend.push_metric() thread safe.
                sample.clear()
                self.backend.push_metric(metric_info, values)
            except Exception as ex:
                LOG.exception(ex)

    def _clear(self):
        self.counter_samples.clear()
        self.timer_samples.clear()

    def do_report(self):
        while True:
            start = time.time()

            LOG.info("Push to backend")
            self._do_report(self.counter_samples)
            self._do_report(self.timer_samples)
            self._clear()

            end = time.time()
            span = end - start

            interval = (CONF.statsd.flush_interval - round(span))
            LOG.info("Pushed, sleep %s" % interval)
            eventlet.sleep(interval)


def main():
    config.parse_args(sys.argv[1:])
    logging.setup('sentry')
    eventlet.monkey_patch(os=False)
    CONF.log_opt_values(LOG, ori_logging.DEBUG)

    pool_size = CONF.statsd.pool_size
    pool = eventlet.GreenPool(pool_size)

    host = CONF.statsd.bind_host
    port = CONF.statsd.bind_port
    buf = CONF.statsd.udp_buffer

    ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ss.bind((host, port))

    LOG.info("Statsd running on %(host)s:%(port)s, pool: %(pool)s" %
             {'host': host, 'port': port, 'pool': pool_size})

    server = StatsServer()
    pool.spawn_n(server.do_report)
    try:
        while True:
            data, addr = ss.recvfrom(buf)
            if data:
                LOG.info("%s %s" % (addr, data.strip()))
                pool.spawn_n(server.process, data)
    except KeyboardInterrupt:
        sys.exit(0)
