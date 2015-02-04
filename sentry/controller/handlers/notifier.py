"""
Notifier other servsers to know NVS's actions.
"""
import copy
from oslo.config import cfg

from sentry import rabbitmq
from sentry.openstack.common import log as logging


LOG = logging.getLogger(__name__)

handler_configs = [
    cfg.BoolOpt('enable_notifier', default=True,
                help="Enable notification about instance deleting"),
    cfg.StrOpt('notifier_rabbit_host', default='$rabbit_host',
                help='The RabbitMQ address which used to notify.'),
    cfg.IntOpt('notifier_rabbit_port', default=5672,
               help="The RabbitMQ port which used to notify"),
    cfg.StrOpt("notifier_rabbit_userid", default='$rabbit_userid',
               help='The RabbitMQ userid to notify'),
    cfg.StrOpt("notifier_rabbit_password", default='$rabbit_password',
               secret=True,
               help='The RabbitMQ password to notify'),
    cfg.StrOpt("notifier_rabbit_virtual_host", default='$rabbit_virtual_host',
               help='The RabbitMQ virtual host to notify'),
    cfg.StrOpt("notifier_exchange", default="nvs_fanout",
               help='The exchange name of nvs notifier.'),
    cfg.IntOpt("notifier_ttl", default=86400,
               help="The expiration of message in seconds, The default is "
               "24 hours"),
]


CONF = cfg.CONF
CONF.register_opts(handler_configs)


class Handler(object):

    def __init__(self):
        if CONF.enable_notifier:
            self.rabbit = rabbitmq.RabbitClient(
                CONF.notifier_rabbit_host,
                CONF.notifier_rabbit_userid,
                CONF.notifier_rabbit_password,
                CONF.notifier_rabbit_virtual_host,
                CONF.notifier_rabbit_port
            )
        else:
            self.rabbit = None

    def handle_message(self, message):
        if self.rabbit is None:
            return

        msg_type = message.get('event_type')

        if not msg_type:
            return

        if msg_type not in ['compute.instance.delete.end']:
            return

        message = copy.deepcopy(message)

        for key in message.keys():
            if key.startswith('_context'):
                message.pop(key)

        LOG.debug("Notifier msg %s" % message)

        exchange = CONF.notifier_exchange
        ttl = 1000 * CONF.notifier_ttl
        self.rabbit.fanout(exchange, message, ttl=ttl)
