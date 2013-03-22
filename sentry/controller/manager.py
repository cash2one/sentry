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
    cfg.StrOpt('nova_sentry_mq_topic',
               default='notifications',
               help='Name of nova notifications topic'),
    cfg.StrOpt('glance_sentry_mq_topic',
               default='glance_notifications',
               help='Name of glance notifications topic'),
    cfg.ListOpt('nova_mq_level_list',
                default=['error', 'info', ],
                help='notifications levels for message queue of nova'),
    cfg.ListOpt('glance_mq_level_list',
                default=['error', 'info', 'warn', ],
                help='notifications levels for message queue of glance'),
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
        nova_topic = CONF.nova_sentry_mq_topic
        glance_topic = CONF.glance_sentry_mq_topic
        controller_hanler = handler.Handler()

        LOG.info('Listening on topic: "%s"' % nova_topic)
        # NOTE(hzyangtk): declare consumer binding on nova exchange
        for nova_level in CONF.nova_mq_level_list:
            nova_queue = self.get_queue_name(nova_topic, nova_level)
            self.conn.declare_topic_consumer(
                    topic=nova_topic,
                    callback=controller_hanler.handle_message,
                    queue_name=nova_queue,
                    exchange_name='nova')
            LOG.debug(_("Listening on the queue: %s") % nova_queue)

        LOG.info('Listening on topic: "%s"' % glance_topic)
        # NOTE(hzyangtk): declare consumer binding on glance exchange
        for glance_level in CONF.glance_mq_level_list:
            glance_queue = self.get_queue_name(glance_topic, glance_level)
            self.conn.declare_topic_consumer(
                    topic=glance_topic,
                    callback=controller_hanler.handle_message,
                    queue_name=glance_queue,
                    exchange_name='glance')
            LOG.debug(_("Listening on the queue: %s") % glance_queue)

        self.conn.consume_in_thread()

    def create(self):
        return eventlet.spawn(self.serve())

    def cleanup(self):
        LOG.info('Cleanup sentry')
        rpc.cleanup()

    def get_queue_name(self, topic, level):
        return '%s.%s' % (topic, level)
