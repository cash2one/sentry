
from eventlet import greenpool
from oslo.config import cfg

from sentry import green
from sentry import messaging
from sentry.openstack.common import log
from sentry.openstack.common import importutils
from sentry.openstack.common import jsonutils

"""
    Sentry listenning on rabbitmq and receive notification
    from nova-compute, nova-service-monitor, nova-cloudwatch,
    nova-network, nova-billing, nova-api, nova-scheduler.
    When received a notification, it will filter the notification
    and send a alarm message to alarm system when the notification
    is alarm level.
"""

CONF = cfg.CONF


manager_opts = [
    cfg.IntOpt("pipeline_pool_size", default=3000,
               help="The max greenthread to process messages."),
]

CONF.register_opts(manager_opts)


LOG = log.getLogger(__name__)


class Pipeline(object):
    """When receive a message, Pipeline will pick a greenthread from pool
    to process the message. Each message will flow from the start handler
    to the end, which means the former may block the latter handlers.
    """

    def __init__(self, pool, handlers):
        """Each handler should define a method `handler_message`, which
        receive one argument to passin the message body.
        """
        self.pool = pool
        self.handlers = handlers

    def sanity_message(self, message):
        if isinstance(message, basestring):
            message = jsonutils.loads(message)
        if not isinstance(message, dict):
            LOG.warn("Message is not a dict object: %s" % message)

        return message

    def process(self, message):
        try:
            message = self.sanity_message(message)

            LOG.debug("Processing message: %s" % message.get('event_type'))

            for handler in self.handlers:
                try:
                    handler.handle_message(message)
                except Exception:
                    LOG.exception("%s process message error, skip it." %
                                  handler)
        except Exception:
            LOG.exception("processing message error.")

    @classmethod
    def create(cls, pool, handler_names):
        prefix = "sentry.notification.handlers"
        class_name = "Handler"
        real_handlers = []
        for name in handler_names:
            path = "%s.%s.%s" % (prefix, name, class_name)
            obj = importutils.import_object(path)
            real_handlers.append(obj)

        return cls(pool, real_handlers)

    def __call__(self, body, message):
        self.pool.spawn_n(self.process, body)
        message.ack()


class Manager(green.GreenletDaemon):
    """Contains a greenthread pool which fire to process incoming messags."""

    def __init__(self):
        LOG.info("Sentry collector start running.")
        self.pool = greenpool.GreenPool(CONF.pipeline_pool_size)

        self.nova_collector = messaging.create_consumer('nova')
        self.glance_collector = messaging.create_consumer('glance')
        self.neutron_collector = messaging.create_consumer('neutron')
        self.cinder_collector = messaging.create_consumer('cinder')
        self.log_error_pipeline = Pipeline.create(self.pool, ['log_error'])

    def setup_consumers(self):
        """Declare queues and binding pipeline to each queue."""

        LOG.info("Declare nova consumers.")
        self.nova_pipeline = Pipeline.create(self.pool,
                                             CONF.nova_event_handlers)
        self.nova_collector.declare_consumer('notifications.info',
                                             self.nova_pipeline)
        self.nova_collector.declare_consumer('notifications.error',
                                             self.nova_pipeline)
        self.nova_collector.declare_consumer('notifications.critical',
                                             self.log_error_pipeline)

        LOG.info("Declare glance consumers")
        self.glance_pipeline = Pipeline.create(self.pool,
                                               CONF.glance_event_handlers)
        self.glance_collector.declare_consumer('glance_notifications.info',
                                               self.glance_pipeline)
        self.glance_collector.declare_consumer('glance_notifications.error',
                                               self.glance_pipeline)
        self.glance_collector.declare_consumer('glance_notifications.warn',
                                               self.glance_pipeline)

        LOG.info("Declare neutron consumers")
        self.neutron_pipeline = Pipeline.create(self.pool,
                                                CONF.neutron_event_handlers)
        self.neutron_collector.declare_consumer('neutron_notifications.info',
                                                self.neutron_pipeline)
        self.neutron_collector.declare_consumer(
            'neutron_notifications.critical', self.log_error_pipeline
        )

        LOG.info("Declare cinder consumers")
        self.cinder_pipeline = Pipeline.create(self.pool,
                                               CONF.cinder_event_handlers)
        self.cinder_collector.declare_consumer('cinder_notifications.info',
                                               self.cinder_pipeline)
        self.cinder_collector.declare_consumer('cinder_notifications.error',
                                               self.cinder_pipeline)
        self.cinder_collector.declare_consumer('cinder_notifications.critical',
                                               self.log_error_pipeline)

    def consume_in_thread(self):
        self.nova_collector.consume_in_thread()
        self.glance_collector.consume_in_thread()
        self.cinder_collector.consume_in_thread()
        self.neutron_collector.consume_in_thread()
