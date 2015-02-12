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
A wrapper for rabbitMQ connection. Each RabbitConnection have own pool and
different config.
"""
from sentry.openstack.common import log as logging
from sentry.openstack.common.rpc import amqp
from sentry.openstack.common.rpc import impl_kombu

LOG = logging.getLogger(__name__)


class RabbitConfig(object):

    def __init__(self):
        """The default values was copy from default config."""
        # Below items not changes frequently
        self.fake_rabbit = False
        self.rabbit_retry_interval = 1
        self.rabbit_max_retries = 0
        self.rabbit_retry_backoff = 2
        self.rabbit_use_ssl = False
        self.rpc_conn_pool_size = 30
        self.kombu_ssl_version = ''
        self.kombu_ssl_keyfile = ''
        self.kombu_ssl_certfile = ''
        self.kombu_ssl_ca_certs = ''

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
                     ha_queue=None):
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
