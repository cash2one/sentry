from sentry.openstack.common import context


class BaseRPCClient(object):

    #NOTE(gtt): Timeout was defined in XXX_rpc_response_timeout

    exchange = None
    namespace = None
    version = '1.0'
    context = context.get_sentry_context()
    service = None

    def _call_bus(self, topic, method, **kwargs):
        return self.bus.call(self.version, self.namespace, self.exchange,
                             self.context, topic, method, **kwargs)
