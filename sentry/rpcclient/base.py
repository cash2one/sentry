from oslo.config import cfg

from sentry.openstack.common import context

CONF = cfg.CONF
rpc_opts = [
    cfg.IntOpt('rpc_timeout',
               default=30,
               help="The timeout in second for RPC calling.")
]
CONF.register_opts(rpc_opts, 'monitor')


class BaseRPCClient(object):

    timeout = CONF.monitor.rpc_timeout
    exchange = None
    namespace = None
    version = '1.0'
    context = context.get_sentry_context()
    service = None

    def _call_bus(self, topic, method, **kwargs):
        return self.bus.call(self.version, self.namespace, self.exchange,
                             self.context, topic, method, timeout=self.timeout,
                             **kwargs)
