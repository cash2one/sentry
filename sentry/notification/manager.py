
import eventlet
from eventlet import greenpool
from oslo.config import cfg

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
]

manager_opts = [
    cfg.IntOpt("pipeline_pool_size", default=3000,
               help="The max greenthread to process messages."),
]

CONF.register_opts(manager_opts)
CONF.register_opts(nova_opts)
CONF.register_opts(cinder_opts)
CONF.register_opts(glance_opts)
CONF.register_opts(neutron_opts)


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

    def __call__(self, message):
        self.pool.spawn_n(self.process, message)


class MessageCollector(object):

    def __init__(self, name, pool):
        self.name = name
        self.pool = pool
        self.rabbit_config = messaging.RabbitConfig.set_defaults(
            rabbit_hosts=self.get_config('rabbit_hosts'),
            rabbit_userid=self.get_config('rabbit_userid'),
            rabbit_password=self.get_config('rabbit_password'),
            rabbit_virtual_host=self.get_config('rabbit_virtual_host'),
            exchange=self.get_config('exchange'),
            durable=self.get_config('rabbit_durable'),
            #auto_delete not used.
            ha_queue=self.get_config('ha_queue'),
        )

    def connect(self):
        self.rabbit = messaging.RabbitEngine(self.rabbit_config)

    def get_config(self, key):
        """Retrieve correct config item from CONF."""
        full_key = '%s_%s' % (self.name, key)
        return getattr(CONF, full_key)

    def declare_consumer(self, routing_key, handler):
        if not hasattr(self, 'rabbit'):
            raise ValueError("Please call connect() first.")

        LOG.debug("Consuming on exchange: %s, routing_key: %s" %
                  (self.rabbit.exchange, routing_key))
        self.rabbit.create_topic_consumer(routing_key, handler)

    def consume_in_thread(self):
        if not hasattr(self, 'rabbit'):
            raise ValueError("Please call connect() first.")

        LOG.debug("Start consuming for %s" % self.name)
        self.rabbit.consume_in_thread()


class Manager(object):
    """Contains a greenthread pool which fire to process incoming messags."""

    def __init__(self):
        LOG.info("Sentry collector start running.")
        self.pool = greenpool.GreenPool(CONF.pipeline_pool_size)

        self.nova_collector = MessageCollector('nova', self.pool)
        self.glance_collector = MessageCollector('glance', self.pool)
        self.neutron_collector = MessageCollector('neutron', self.pool)
        self.cinder_collector = MessageCollector('cinder', self.pool)
        self.log_error_pipeline = Pipeline.create(self.pool, ['log_error'])

    def serve(self):
        """Declare queues and binding pipeline to each queue."""

        LOG.info("Declare nova consumers.")
        self.nova_pipeline = Pipeline.create(self.pool,
                                             CONF.nova_event_handlers)
        self.nova_collector.connect()
        self.nova_collector.declare_consumer('notifications.info',
                                             self.nova_pipeline)
        self.nova_collector.declare_consumer('notifications.error',
                                             self.nova_pipeline)
        self.nova_collector.declare_consumer('notifications.critical',
                                             self.log_error_pipeline)

        LOG.info("Declare glance consumers")
        self.glance_pipeline = Pipeline.create(self.pool,
                                               CONF.glance_event_handlers)
        self.glance_collector.connect()
        self.glance_collector.declare_consumer('glance_notifications.info',
                                               self.glance_pipeline)
        self.glance_collector.declare_consumer('glance_notifications.error',
                                               self.glance_pipeline)
        self.glance_collector.declare_consumer('glance_notifications.warn',
                                               self.glance_pipeline)

        LOG.info("Declare neutron consumers")
        self.neutron_pipeline = Pipeline.create(self.pool,
                                                CONF.neutron_event_handlers)
        self.neutron_collector.connect()
        self.neutron_collector.declare_consumer('neutron_notifications.info',
                                                self.neutron_pipeline)
        self.neutron_collector.declare_consumer(
            'neutron_notifications.critical', self.log_error_pipeline
        )

        LOG.info("Declare cinder consumers")
        self.cinder_pipeline = Pipeline.create(self.pool,
                                               CONF.cinder_event_handlers)
        self.cinder_collector.connect()
        self.cinder_collector.declare_consumer('cinder_notifications.info',
                                               self.cinder_pipeline)
        self.cinder_collector.declare_consumer('cinder_notifications.error',
                                               self.cinder_pipeline)
        self.cinder_collector.declare_consumer('cinder_notifications.critical',
                                               self.log_error_pipeline)

    def run_server(self):
        self.serve()

    def _loop(self):
        """A infinite loop to block the thread not exit."""
        while True:
            eventlet.sleep(0.1)

    def wait(self):
        self.nova_collector.consume_in_thread()
        self.glance_collector.consume_in_thread()
        self.cinder_collector.consume_in_thread()
        self.neutron_collector.consume_in_thread()
        LOG.info("Sentry start waiting.")
        try:
            self.pool.spawn(self._loop)
            self.pool.waitall()
        except KeyboardInterrupt:
            LOG.info("KeyboardInterrupt received, Exit.")
