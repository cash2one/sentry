#
# Created on 2012-11-16
#
# @author: hzyangtk
#

import eventlet
from eventlet import greenpool

from sentry.controller import handler
from sentry.openstack.common import cfg
from sentry.openstack.common import log
from sentry.openstack.common import rpc

"""
    Sentry listenning on rabbitmq and receive notification
    from nova-compute, nova-service-monitor, nova-cloudwatch,
    nova-network, nova-billing, nova-api, nova-scheduler.
    When received a notification, it will filter the notification
    and send a alarm message to alarm system when the notification
    is alarm level.
"""


manager_configs = [
    cfg.StrOpt('queue_suffix',
               default='sentry',
               help='Name of queue suffix'),
    cfg.StrOpt('nova_notifications_topic',
               default='notifications.*',
               help='Name of nova notifications topic'),
    cfg.StrOpt('glance_notifications_topic',
               default='glance_notifications.error',
               help='Name of glance notifications topic'),
]


CONF = cfg.CONF
CONF.register_opts(manager_configs)
LOG = log.getLogger(__name__)


class Manager(object):

    def __init__(self):
        self.conn = rpc.create_connection(new=True)

    def serve(self):
        """
        The default notification topic is:
            "topic = '%s.%s' % (topic, priority)"

        Example:
            "notifications.info"
        """
        LOG.info('Start sentry')
        nova_topic = CONF.nova_notifications_topic
        glance_topic = CONF.glance_notifications_topic
        controller_hanler = handler.Handler()

        LOG.info('Queue: "%s" listen on topic: "%s"' %
                 (self.get_queue_name(nova_topic), nova_topic))
        # NOTE(hzyangtk): declare consumer binding on nova exchange
        self.conn.declare_topic_consumer(
                topic=nova_topic, callback=controller_hanler.handle_message,
                queue_name=self.get_queue_name(nova_topic),
                exchange_name='nova')

        LOG.info('Queue: "%s" listen on topic: "%s"' %
                 (self.get_queue_name(nova_topic), glance_topic))
        # NOTE(hzyangtk): declare consumer binding on glance exchange
        self.conn.declare_topic_consumer(
                topic=glance_topic, callback=controller_hanler.handle_message,
                queue_name=self.get_queue_name(nova_topic),
                exchange_name='glance')

        self.conn.consume_in_thread()

    def create(self):
        return eventlet.spawn(self.serve())

    def cleanup(self):
        LOG.info('Cleanup sentry')
        rpc.cleanup()

    def get_queue_name(self, topic):
        return '%s_%s' % (topic, CONF.queue_suffix)
