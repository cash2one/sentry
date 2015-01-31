
import functools
import eventlet
from kombu import entity
from oslo.config import cfg

from sentry.openstack.common import log
from sentry.openstack.common import rpc
from sentry.openstack.common import importutils
from sentry.openstack.common import jsonutils
from sentry.openstack.common.rpc import impl_kombu

"""
    Sentry listenning on rabbitmq and receive notification
    from nova-compute, nova-service-monitor, nova-cloudwatch,
    nova-network, nova-billing, nova-api, nova-scheduler.
    When received a notification, it will filter the notification
    and send a alarm message to alarm system when the notification
    is alarm level.
"""


manager_configs = [
    cfg.BoolOpt("ack_on_error", default=False,
                help="Whether to ack the message if process failed, "
                "default is False."),
    cfg.StrOpt('nova_sentry_mq_topic',
               default='notifications',
               help='Name of nova notifications topic'),
    cfg.StrOpt('glance_sentry_mq_topic',
               default='glance_notifications',
               help='Name of glance notifications topic'),
    cfg.StrOpt('neutron_sentry_mq_topic',
               default='neutron_notifications',
               help='Name of neutron notifications topic'),
    cfg.StrOpt('cinder_sentry_mq_topic',
               default='cinder_notifications',
               help='Name of neutron notifications topic'),
    cfg.ListOpt('nova_mq_level_list',
                default=['error', 'info'],
                help='notifications levels for message queue of nova'),
    cfg.ListOpt('glance_mq_level_list',
                default=['error', 'info'],
                help='notifications levels for message queue of glance'),
    cfg.ListOpt('neutron_mq_level_list',
                default=['error', 'info'],
                help='notifications levels for message queue of neutron'),
    cfg.ListOpt('cinder_mq_level_list',
                default=['error', 'info'],
                help='notifications levels for message queue of neutron'),

    cfg.BoolOpt('cinder_durable',
                default=False,
                help="cinder notification durable"),
    cfg.BoolOpt('nova_durable',
                default=False,
                help="nova notification durable"),
    cfg.BoolOpt('neutron_durable',
                default=False,
                help="neutron notification durable"),
    cfg.BoolOpt('glance_durable',
                default=False,
                help="neutron notification durable"),
]

handlers = [
    cfg.ListOpt('nova_event_handlers',
                default=['alarm', 'nova', 'notifier'],
                help="Nova event handlers"),
    cfg.ListOpt('cinder_event_handlers',
                default=['cinder'],
                help="cinder event handlers"),
    cfg.ListOpt('neutron_event_handlers',
                default=['neutron'],
                help="neutron event handlers"),
    cfg.ListOpt('glance_event_handlers',
                default=['glance'],
                help="glance event handlers"),
]

CONF = cfg.CONF
CONF.register_opts(manager_configs)
CONF.register_opts(handlers)
LOG = log.getLogger(__name__)


class Pipeline(object):
    def __init__(self, handlers):
        self.handlers = handlers

    def process(self, message):
        if isinstance(message, basestring):
            message = jsonutils.loads(message)
        if not isinstance(message, dict):
            LOG.warn("Message is not a dict object: %s" % message)

        LOG.debug("Processing message: %s" % message['event_type'])
        for handler in self.handlers:
            try:
                handler.handle_message(message)
            except Exception:
                LOG.exception("%s process message error, skip it." % handler)


class Manager(object):

    def __init__(self):
        self.thread = None
        # faild early
        self.nova_handlers = self.registry_handlers(
            CONF.nova_event_handlers)
        self.nova_pipeline = Pipeline(self.nova_handlers)

        self.cinder_handlers = self.registry_handlers(
            CONF.cinder_event_handlers)
        self.cinder_pipeline = Pipeline(self.cinder_handlers)

        self.neutron_handlers = self.registry_handlers(
            CONF.neutron_event_handlers)
        self.neutron_pipeline = Pipeline(self.neutron_handlers)

        self.glance_handlers = self.registry_handlers(
            CONF.glance_event_handlers)
        self.glance_pipeline = Pipeline(self.glance_handlers)

    def registry_handlers(self, handler_names):
        prefix = "sentry.controller.handlers"
        class_name = "Handler"
        real_handlers = []
        for name in handler_names:
            path = "%s.%s.%s" % (prefix, name, class_name)
            try:
                obj = importutils.import_object(path)
                real_handlers.append(obj)
            except ImportError:
                LOG.exception("import %(path)s error, ignore this handler" %
                              {'path': path})
        return real_handlers

    def serve(self):
        """
        The default notification topic is:
            "topic = '%s.%s' % (topic, priority)"

        Example:
            "notifications.info"
        """
        LOG.info('Start sentry service.')
        self.conn = rpc.create_connection(new=True)

        # Nova
        self._declare_queue_consumer(
            CONF.nova_mq_level_list,
            CONF.nova_sentry_mq_topic,
            self.nova_pipeline.process,
            'nova-sentry',
            durable=CONF.nova_durable,
        )

        # neutron
        self._declare_queue_consumer(
            CONF.neutron_mq_level_list,
            CONF.neutron_sentry_mq_topic,
            self.neutron_pipeline.process,
            'neutron-sentry',
            durable=CONF.neutron_durable,
        )

        # glance
        self._declare_queue_consumer(
            CONF.glance_mq_level_list,
            CONF.glance_sentry_mq_topic,
            self.glance_pipeline.process,
            'glance-sentry',
            durable=CONF.glance_durable,
        )

        # cinder
        self._declare_queue_consumer(
            CONF.cinder_mq_level_list,
            CONF.cinder_sentry_mq_topic,
            self.cinder_pipeline.process,
            'cinder-sentry',
            durable=CONF.cinder_durable,
        )

        self.conn.consume_in_thread()
        LOG.info('Start consuming notifications.')

    def _clean_exchange(self, name):
        LOG.debug("cleanup exchange %s" % name)
        ex = entity.Exchange(name=name, channel=self.conn.get_channel())
        try:
            ex.delete()
        except Exception as ex:
            LOG.warn("Cleanup exchange failed. %s" % ex)

    def _declare_queue_consumer(self, levels, topic, handler, exchange,
                        durable=False, auto_delete=False, exclusive=False,
                        ha_queue=False):

        self._clean_exchange(exchange)

        for level in levels:
            queue = '%s.%s' % (topic, level)

            kwargs = dict(
                name=queue,
                ack_on_error=CONF.ack_on_error,
                exchange_name=exchange,
                durable=durable,
                auto_delete=auto_delete,
                exclusive=exclusive,
            )

            if ha_queue:
                kwargs['queue_arguments'] = {'x-ha-policy': 'all'}

            self.conn.declare_consumer(
                functools.partial(impl_kombu.TopicConsumer, **kwargs),
                topic, handler)
            LOG.debug("Declare queue name: %(queue)s, topic: %(topic)s" %
                      {"queue": queue, "topic": topic})

    def run_server(self):
        self.thread = eventlet.spawn(self.serve)

    def wait(self):
        if self.thread is None:
            raise Exception('Must calling run_server() before wait().')

        try:
            self.thread.wait()
        except KeyboardInterrupt:
            LOG.info("KeyboardInterrupt received, Exit.")

    def cleanup(self):
        LOG.info('Cleanup sentry')
        rpc.cleanup()
