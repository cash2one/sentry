from oslo.config import cfg
from eventlet import semaphore

from sentry.messaging import common
from sentry.messaging import rabbit
from sentry.messaging import rpc
from sentry.messaging.rpc import RabbitEngine
from sentry.messaging.common import RabbitConfig
from sentry.messaging.rabbit import KombuPublisher

__all__ = [
    'RabbitConfig', 'RabbitEngine', 'KombuPublisher',
    'nova_bus', 'cinder_bus', 'neutron_bus', 'glance_bus', 'create_consumer',
]

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
    cfg.ListOpt('neutron_critical_event_handlers',
                default=['log_error', 'neutron_monitor'],
                help="Neutron critical event handlers"),
    cfg.IntOpt('neutron_rpc_response_timeout',
               default=60,
               help='Seconds to wait for a response from call or multicall'),
]

CONF.register_opts(nova_opts)
CONF.register_opts(cinder_opts)
CONF.register_opts(glance_opts)
CONF.register_opts(neutron_opts)


class Factory(object):
    """A single instance factory, all object was store in class level.

    """

    _sem = semaphore.Semaphore()
    valid_names = ('nova', 'glance', 'neutron', 'cinder')
    consumers = {}
    rpc_clients = {}

    @classmethod
    def _validate_name(cls, name):
        if name not in cls.valid_names:
            raise ValueError("name should be one of %s" % cls.valid_names)

    @classmethod
    def create_consumer(cls, name):
        """Return message consumer ``KombuConsumer``."""
        cls._validate_name(name)

        with cls._sem:
            if name not in cls.consumers:
                config = common.RabbitConfig.factory(name)
                c = rabbit.KombuConsumer(config)
                cls.consumers[name] = c

        return cls.consumers[name]

    @classmethod
    def create_rpc_client(cls, name):
        """Return an ``RabbitEngine`` object."""
        cls._validate_name(name)

        with cls._sem:
            if name not in cls.rpc_clients:
                config = common.RabbitConfig.factory(name)
                client = rpc.RabbitEngine(config)
                cls.rpc_clients[name] = client

        return cls.rpc_clients[name]


def nova_bus():
    return Factory.create_rpc_client('nova')


def cinder_bus():
    return Factory.create_rpc_client('cinder')


def glance_bus():
    return Factory.create_rpc_client('glance')


def neutron_bus():
    return Factory.create_rpc_client('neutron')


def create_consumer(name):
    return Factory.create_consumer(name)
