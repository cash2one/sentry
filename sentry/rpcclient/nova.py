from sentry.rpcclient import base
from sentry import messaging

__all__ = [
    'NovaConsoleauthRPCClient',
    'NovaComputeRPCClient',
    'NovaSchedulerRPCClient',
    'NovaConductorRPCClient',
]


class NovaRPCClient(base.BaseRPCClient):

    exchange = 'nova'
    version = '1.0'

    def __init__(self):
        self.bus = messaging.nova_bus()

    def _topic(self, host):
        return '%s.%s' % (self.service, host)

    def get_backdoor_port(self, host):
        """Return None, if timeout means target host was down."""
        topic = self._topic(host)
        method = 'get_backdoor_port'
        return self._call_bus(topic, method)


class NovaConductorRPCClient(NovaRPCClient):
    version = '1.58'
    service = 'conductor'


class NovaComputeRPCClient(NovaRPCClient):
    version = '2.0'
    service = 'compute'


class NovaSchedulerRPCClient(NovaRPCClient):
    version = '2.0'
    service = 'scheduler'


class NovaConsoleauthRPCClient(NovaRPCClient):
    version = '1.0'
    service = 'consoleauth'
