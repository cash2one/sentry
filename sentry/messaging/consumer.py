"""
Notification consumers.

Nova:

    Exchange: nova
    Queue: notifications.info (routing_key: notifications.info)
    Queue: notifications.error (routing_key: notifications.error)

Cinder:

    Exchange: openstack
    Queue: cinder_notifications.info (routing_key: cinder_notifications.info)
    Queue: cinder_notifications.error (routing_key: cinder_notifications.error)

Neutron:

  Exchange: neutron
  Queue: neutron_notifications.info (routing_key: neutron_notifications.info)
  Queue: neutron_notifications.error (routing_key: neutron_notifications.error)

"""
import collections

import eventlet
import kombu
from kombu import mixins

from sentry.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class KombuConsumer(mixins.ConsumerMixin):

    def __init__(self, config):
        self._config = config
        self._init_connection(config)

        self._exchange = kombu.Exchange(
            config.control_exchange,
            durable=config.amqp_durable_queues,
            auto_delete=config.amqp_auto_delete,
            type='topic',
        )
        # key is callback, value is a list of queue.
        self._consumers = collections.defaultdict(lambda: [])

    def get_consumers(self, Consumer, channel):
        """Overide ConsumerMixin"""
        consumers = []
        for callback, queues in self._consumers.iteritems():
            consumer = Consumer(queues=queues, callbacks=[callback])
            consumers.append(consumer)
            LOG.debug("%s" % consumer)
        return consumers

    def declare_consumer(self, queue_name, callback):
        queue = kombu.Queue(
            queue_name,
            self._exchange,
            routing_key=queue_name,
            durable=self._config.amqp_durable_queues,
            auto_delete=self._config.amqp_auto_delete,
            exclusive=False,     # oslo.messaging set it to False
        )
        self._consumers[callback].append(queue)

    def _init_connection(self, config):
        hosts = config.rabbit_hosts
        userid = config.rabbit_userid
        password = config.rabbit_password
        vhost = config.rabbit_virtual_host

        urls = []
        for host in hosts:
            url = ('amqp://%(userid)s:%(password)s@%(host)s/%(vhost)s' %
                   {'userid': userid, 'password': password,
                    'host': host, 'vhost': vhost})
            urls.append(url)

        urls = ';'.join(urls)
        self.connection = kombu.Connection(
            urls, failover_strategy='round-robin', connect_timeout=5
        )

    def consume_in_thread(self):
        eventlet.spawn(self.run)
        eventlet.sleep(0)

    def run(self, _tokens=1):
        # Override ConsumerMixin's run() to report exception detail.
        restart_limit = self.restart_limit
        errors = (self.connection.connection_errors +
                  self.connection.channel_errors)
        while not self.should_stop:
            try:
                if restart_limit.can_consume(_tokens):
                    for _ in self.consume(limit=None):  # pragma: no cover
                        pass
                else:
                    eventlet.sleep(restart_limit.expected_time(_tokens))
            except errors as ex:
                LOG.warn('Connection to broker lost. '
                         'Trying to re-establish the connection... %s' % ex)


if __name__ == '__main__':

    def foo(a, b):
        b.ack()
        print a, b

    import logging
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    from sentry import messaging
    from sentry import kombuit

    config = messaging.RabbitConfig()
    config.rabbit_hosts = ['127.0.0.1:5672']
    config.rabbit_userid = 'guest'
    config.rabbit_password = 'ntse'
    config.control_exchange = 'nova'
    consumer = kombuit.KombuConsumer(config)
    consumer.declare_consumer('notifications.info', foo)
    consumer.declare_consumer('notifications.critical', foo)
    consumer.consume_in_thread()
