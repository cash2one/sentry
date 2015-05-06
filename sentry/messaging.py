# Copyright 2015 Netease Corp.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""
Sentry listen on message bus to communite with OpenStack compoments(Nova,
Glance, Neutron, etc.). Each compoment may have different RabbitMQ Server,
so here we define individual configs for each compoment.

Please using `RabbitEngine` if you need fine control of messages.

If you just want communite with OpenStack compoment, like Nova, please
calling nova_bus() to get `MessageBus` object, which have ready communited with
OpenStack's RabbitMQ.
"""

from oslo.config import cfg
from eventlet import semaphore

#FIXME: After Kilo published, need to transfer to based on oslo.messaging
from sentry.openstack.common import log as logging
from sentry.openstack.common.rpc import amqp
from sentry.openstack.common.rpc import impl_kombu

LOG = logging.getLogger(__name__)
CONF = cfg.CONF

CONF.import_opt('rabbit_hosts', 'sentry.openstack.common.rpc.impl_kombu')
CONF.import_opt('rabbit_userid', 'sentry.openstack.common.rpc.impl_kombu')
CONF.import_opt('rabbit_password', 'sentry.openstack.common.rpc.impl_kombu')
CONF.import_opt('rabbit_virtual_host',
                'sentry.openstack.common.rpc.impl_kombu')

nova_opts = [
    cfg.ListOpt('nova_rabbit_hosts',
                default=CONF.rabbit_hosts,
                deprecated_name='rabbit_hosts',
                help="Nova rabbit broker hosts."),
    cfg.StrOpt('nova_exchange',
               default='nova',
               help="Nova rabbit exchange name."),
    cfg.StrOpt('nova_rabbit_userid',
               default='$rabbit_userid',
               help="Nova rabbit userid."),
    cfg.StrOpt('nova_rabbit_password',
               default='$rabbit_password',
               secret=True,
               help="Nova rabbit password."),
    cfg.StrOpt('nova_rabbit_virtual_host',
               default='$rabbit_virtual_host',
               help="Nova rabbit virtual host."),
    cfg.BoolOpt('nova_rabbit_durable',
                default=False,
                help="nova rabbit durable"),
    cfg.BoolOpt('nova_ha_queue',
                deprecated_name='rabbit_ha_queues',
                default=False,
                help="nova HA queues"),
    cfg.ListOpt('nova_event_handlers',
                default=['nova', 'notifier', 'bi_log'],
                help="Nova event handlers"),
    cfg.IntOpt('nova_rpc_response_timeout',
               default=60,
               help='Seconds to wait for a response from call or multicall'),
]

glance_opts = [
    cfg.ListOpt('glance_rabbit_hosts',
                default=CONF.rabbit_hosts,
                deprecated_name='rabbit_hosts',
                help="Glance rabbit broker hosts."),
    cfg.StrOpt('glance_exchange',
               default='glance',
               help="Glance rabbit exchange name."),
    cfg.StrOpt('glance_rabbit_userid',
               default='$rabbit_userid',
               help="Glance rabbit userid."),
    cfg.StrOpt('glance_rabbit_password',
               default='$rabbit_password',
               secret=True,
               help="Glance rabbit password."),
    cfg.StrOpt('glance_rabbit_virtual_host',
               default='$rabbit_virtual_host',
               help="Glance rabbit virtual host."),
    cfg.BoolOpt('glance_rabbit_durable',
                default=False,
                help="Glance rabbit durable"),
    cfg.BoolOpt('glance_ha_queue',
                default=False,
                deprecated_name='rabbit_ha_queues',
                help="Glance HA queues"),
    cfg.ListOpt('glance_event_handlers',
                default=['glance', 'bi_log'],
                help="Glance event handlers"),
    cfg.IntOpt('glance_rpc_response_timeout',
               default=60,
               help='Seconds to wait for a response from call or multicall'),
]

cinder_opts = [
    cfg.ListOpt('cinder_rabbit_hosts',
                default=CONF.rabbit_hosts,
                deprecated_name='rabbit_hosts',
                help="Cinder rabbit broker hosts."),
    cfg.StrOpt('cinder_exchange',
               default='openstack',
               help="Cinder rabbit exchange name."),
    cfg.StrOpt('cinder_rabbit_userid',
               default='$rabbit_userid',
               help="Cinder rabbit userid."),
    cfg.StrOpt('cinder_rabbit_password',
               default='$rabbit_password',
               secret=True,
               help="Cinder rabbit password."),
    cfg.StrOpt('cinder_rabbit_virtual_host',
               default='$rabbit_virtual_host',
               help="Cinder rabbit virtual host."),
    cfg.BoolOpt('cinder_rabbit_durable',
                default=False,
                help="Cinder rabbit durable"),
    cfg.BoolOpt('cinder_ha_queue',
                default=False,
                deprecated_name='rabbit_ha_queues',
                help="Cinder HA queues"),
    cfg.ListOpt('cinder_event_handlers',
                default=['cinder', 'bi_log'],
                help="Cinder event handlers"),
    cfg.IntOpt('cinder_rpc_response_timeout',
               default=60,
               help='Seconds to wait for a response from call or multicall'),
]

neutron_opts = [
    cfg.ListOpt('neutron_rabbit_hosts',
                default=CONF.rabbit_hosts,
                deprecated_name='rabbit_hosts',
                help="Neutron rabbit broker hosts."),
    cfg.StrOpt('neutron_exchange',
               default='neutron',
               help="Neutron rabbit exchange name."),
    cfg.StrOpt('neutron_rabbit_userid',
               default='$rabbit_userid',
               help="Neutron rabbit userid."),
    cfg.StrOpt('neutron_rabbit_password',
               default='$rabbit_password',
               secret=True,
               help="Neutron rabbit password."),
    cfg.StrOpt('neutron_rabbit_virtual_host',
               default='$rabbit_virtual_host',
               help="Neutron rabbit virtual host."),
    cfg.BoolOpt('neutron_rabbit_durable',
                deprecated_name='neutron_durable',
                default=False,
                help="Neutron rabbit durable"),
    cfg.BoolOpt('neutron_ha_queue',
                default=False,
                deprecated_name='rabbit_ha_queues',
                help="Neutron HA queues"),
    cfg.ListOpt('neutron_event_handlers',
                default=['neutron', 'bi_log'],
                help="Neutron event handlers"),
    cfg.IntOpt('neutron_rpc_response_timeout',
               default=60,
               help='Seconds to wait for a response from call or multicall'),
]

CONF.register_opts(nova_opts)
CONF.register_opts(cinder_opts)
CONF.register_opts(glance_opts)
CONF.register_opts(neutron_opts)


class RabbitConfig(object):

    def __init__(self):
        """The default values was copy from default config."""
        # Below items not changes frequently
        self.fake_rabbit = False
        self.rabbit_retry_interval = 1
        self.rabbit_max_retries = 0
        self.rabbit_retry_backoff = 2
        self.rabbit_use_ssl = False
        self.rpc_conn_pool_size = 10
        self.kombu_ssl_version = ''
        self.kombu_ssl_keyfile = ''
        self.kombu_ssl_certfile = ''
        self.kombu_ssl_ca_certs = ''
        self.rpc_response_timeout = 60

        # Below items should be change before using.
        self.rabbit_host = 'localhost'
        self.rabbit_port = 5672

        default_host = '%s:%s' % (self.rabbit_host, self.rabbit_port)
        self.rabbit_hosts = [default_host]

        self.rabbit_userid = 'guest'
        self.rabbit_password = 'guest'
        self.rabbit_virtual_host = '/'
        self.amqp_durable_queues = False
        self.amqp_auto_delete = False
        self.rabbit_ha_queues = True
        self.control_exchange = 'openstack'

    @classmethod
    def set_defaults(cls, rabbit_hosts=None, rabbit_userid=None,
                     rabbit_password=None, rabbit_virtual_host=None,
                     exchange=None, durable=None, auto_delete=None,
                     ha_queue=None, rpc_response_timeout=None):
        config = cls()

        if rabbit_hosts is not None:
            config.rabbit_hosts = rabbit_hosts

        if rabbit_userid is not None:
            config.rabbit_userid = rabbit_userid

        if rabbit_password is not None:
            config.rabbit_password = rabbit_password

        if rabbit_virtual_host is not None:
            config.rabbit_virtual_host = rabbit_virtual_host

        if exchange is not None:
            config.control_exchange = exchange

        if durable is not None:
            config.amqp_durable_queues = durable

        if auto_delete is not None:
            config.amqp_auto_delete = auto_delete

        if ha_queue is not None:
            config.rabbit_ha_queues = ha_queue

        if rpc_response_timeout is not None:
            config.rpc_response_timeout = rpc_response_timeout

        return config


class RabbitEngine(object):
    """An Engine contains a pool of connections."""

    def __init__(self, conf):
        """When instantiation engine will connect to rabbit server.

        :param conf: An instance of `RabbitConfig`
        """
        if not isinstance(conf, RabbitConfig):
            msg = "Param `conf` Should be a `RabbitConfig` instance."
            raise ValueError(msg)

        self.conf = conf
        # connection in pool only used for RPC. While self._connection
        # only used for listen on notification.
        self.pool = self._create_pool(conf)
        self._connection = self._single_connection(self.conf, self.pool)

    def _create_pool(self, conf):
        return amqp.Pool(conf, impl_kombu.Connection)

    def _single_connection(self, conf, pool):
        """Return a ConnectionContext, the long life connection is just for
        consumer.
        """
        return amqp.ConnectionContext(conf, pool, False)

    @property
    def connection(self):
        return self._connection

    @property
    def exchange(self):
        return self.conf.control_exchange

    def consume_in_thread(self):
        """Spawn a greenlet to consume messages."""
        self.connection.consume_in_thread()

    def create_topic_consumer(self, routing_key, handler, queue_name=None,
                              exchange_name=None, ack_on_error=True):
        """Declare a consumer on a topic type exchange.

        queue_name will be the same with ``topic`` if not explicity specified.
        exchange_name will get from config object if not explicity specified.
        routing_key will be the same with ``topic`` if not explicity specified.

        :param routing_key: String, routing_key queue binding with exchange.
        :param proxy: Callable, when receive message from broker, calling
                      proxy.
        :param queue_name: String, defaults to routing_key.
        :param exchange_name: String, if not specified, will get from config.
        :param ack_on_error: boolean, whether ack if exception happend.
        """
        self.connection.declare_topic_consumer(routing_key,
                                               handler,
                                               queue_name=queue_name,
                                               exchange_name=exchange_name,
                                               ack_on_error=ack_on_error)

    def fanout(self, topic, msg, ttl=None):
        """Using fanout exchange to send a message. The exchange name is NOT
        get from config object, gets from ``topic``.

        :param topic: string, the exchange name will be '$(topic)_fanout'.
        :param msg: string, the message content
        :param ttl: int, the life time of message in seconds
        """
        LOG.debug("Fanout success on topic '%s'." % topic)
        exchange_options = {'durable': False,
                            'auto_delete': False,
                            'exclusive': False}
        with amqp.ConnectionContext(self.conf, self.pool) as conn:
            conn.publisher_send(impl_kombu.FanoutPublisher, topic, msg,
                                timeout=ttl, **exchange_options)

    def _call(self, context, exchange, topic, msg, timeout=None):
        """Sends a message on a topic and wait for a response.

        :param context: The OpenStack context object.
        :param exchange: String, the default exchange is 'openstack'.
        :param topic: String, the topic of rpc request to used.
        :param msg: Message body.
        :timeout: Integer, rpc timeout.
        """
        self.conf.control_exchange = exchange
        return amqp.call(self.conf, context, topic, msg, timeout, self.pool)

    def call(self, version, namespace, exchange, context, topic,
             method, timeout, **kwargs):
        payload = {}
        payload['version'] = version
        payload['namespace'] = namespace
        payload['method'] = method
        payload['args'] = kwargs
        return self._call(context, exchange, topic, payload, timeout)


class MessageBus(object):
    """Each OpenStack compoment have individual message bus

    Just a scaffold to create `RabbitEngine` object from config files.
    """

    def __init__(self, name):
        self.name = name
        self.rabbit_config = RabbitConfig.set_defaults(
            rabbit_hosts=self.get_config('rabbit_hosts'),
            rabbit_userid=self.get_config('rabbit_userid'),
            rabbit_password=self.get_config('rabbit_password'),
            rabbit_virtual_host=self.get_config('rabbit_virtual_host'),
            exchange=self.get_config('exchange'),
            durable=self.get_config('rabbit_durable'),
            #auto_delete not used.
            ha_queue=self.get_config('ha_queue'),
            rpc_response_timeout=self.get_config('rpc_response_timeout'),
        )

    def connect(self):
        self.rabbit = RabbitEngine(self.rabbit_config)

    def get_config(self, key):
        """Retrieve correct config item from CONF."""
        full_key = '%s_%s' % (self.name, key)
        return getattr(CONF, full_key)

    def declare_consumer(self, routing_key, handler):
        LOG.debug("Consuming on exchange: %s, routing_key: %s" %
                  (self.rabbit.exchange, routing_key))

        return self._check_rabbit_then_calling(
            'create_topic_consumer', routing_key, handler
        )

    def consume_in_thread(self):
        LOG.debug("Start consuming for %s" % self.name)
        return self._check_rabbit_then_calling('consume_in_thread')

    def call(self, *args, **kwargs):
        return self._check_rabbit_then_calling('call', *args, **kwargs)

    def _check_rabbit_then_calling(self, method, *args, **kwargs):
        if not hasattr(self, 'rabbit'):
            raise ValueError("Please call connect() first.")

        func = getattr(self.rabbit, method)
        return func(*args, **kwargs)


NOVA_BUS = None
CINDER_BUS = None
NEUTRON_BUS = None
GLANCE_BUS = None

_create_sem = semaphore.Semaphore()


def nova_bus():
    global NOVA_BUS
    with _create_sem:
        if not NOVA_BUS:
            NOVA_BUS = MessageBus('nova')
            NOVA_BUS.connect()

    return NOVA_BUS


def cinder_bus():
    global CINDER_BUS

    with _create_sem:
        if not CINDER_BUS:
            CINDER_BUS = MessageBus('cinder')
            CINDER_BUS.connect()

    return CINDER_BUS


def glance_bus():
    global GLANCE_BUS

    with _create_sem:
        if not GLANCE_BUS:
            GLANCE_BUS = MessageBus('glance')
            GLANCE_BUS.connect()

    return GLANCE_BUS


def neutron_bus():
    global NEUTRON_BUS

    with _create_sem:
        if not NEUTRON_BUS:
            NEUTRON_BUS = MessageBus('neutron')
            NEUTRON_BUS.connect()

    return NEUTRON_BUS
