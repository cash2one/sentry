from oslo.config import cfg

CONF = cfg.CONF


class RabbitConfig(object):

    @classmethod
    def factory(cls, name):
        """A scaffold to create RabbitConfig object for OpenStack compoments.

        """

        def get_config(key):
            full_key = '%s_%s' % (name, key)
            return getattr(CONF, full_key)

        return cls.set_defaults(
            rabbit_hosts=get_config('rabbit_hosts'),
            rabbit_userid=get_config('rabbit_userid'),
            rabbit_password=get_config('rabbit_password'),
            rabbit_virtual_host=get_config('rabbit_virtual_host'),
            exchange=get_config('exchange'),
            durable=get_config('rabbit_durable'),
            ha_queue=get_config('ha_queue'),
            rpc_response_timeout=get_config('rpc_response_timeout'),
        )

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
        self.kombu_reconnect_delay = 1.0
        self.kombu_transport = 'pyamqp'
        self.kombu_keepalive_enable = True
        self.kombu_keepalive_idle = 30
        self.kombu_keepalive_interval = 3
        self.kombu_keepalive_count = 3

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
