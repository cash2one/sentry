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
Sentry listen on message bus to communicate with OpenStack compoments (Nova,
Glance, Neutron, etc.). Each compoment may have different RabbitMQ Server,
so here we define individual configs for each compoment.

To be a message consumer, sentry based on kombu 2.5. Whilist to be a RPC
caller sentry using openstack.common.rpc (oslo.messaging). The reason
why sentry barely using kombu is to work around a bug:

    https://bugs.launchpad.net/ceilometer/+bug/1337715

Also, because OpenStack need to implement different message driver, like
RabbitMQ, ZeroMQ, etc. oslo.messaging is sophisticated. Sentry do not
need this sophisticated, it just using RabbitMQ, so barely using kombu
is a good choice.
"""

from sentry.messaging import common
from sentry.openstack.common import log as logging
#FIXME: After Kilo published, need to transfer to based on oslo.messaging
from sentry.openstack.common.rpc import amqp
from sentry.openstack.common.rpc import impl_kombu

LOG = logging.getLogger(__name__)


class RPCClient(object):
    """RPCClient contains a pool of connections to invoking requests."""

    def __init__(self, conf):
        """When instantiation engine will connect to rabbit server.

        :param conf: An instance of `RabbitConfig`
        """
        if not isinstance(conf, common.RabbitConfig):
            msg = "Param `conf` Should be a `RabbitConfig` instance."
            raise ValueError(msg)

        self.conf = conf
        # connection in pool only used for RPC. While self._connection
        # only used for listen on notification.
        self.pool = self._create_pool(conf)

    def _create_pool(self, conf):
        return amqp.Pool(conf, impl_kombu.Connection)

    @property
    def exchange(self):
        return self.conf.control_exchange

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

RabbitEngine = RPCClient
