from sentry.rpcclient import base
from sentry import messaging


__all__ = [
    'NeutronDHCPAgentRPCClient',
    'NeutronL3AgentRPCClient',
    'NeutronMonitorAgentRPCClient',
    'NeutronOvsAgentRPCClient',
]


class NeutronRPCClient(base.BaseRPCClient):

    exchange = 'neutron'
    version = '1.0'

    def __init__(self):
        self.bus = messaging.neutron_bus()

    def _topic(self, host):
        return '%s.%s' % (self.service, host)

    def ping(self, host):
        topic = self._topic(host)
        return self._call_bus(topic, 'ping')


class NeutronDHCPAgentRPCClient(NeutronRPCClient):
    service = 'dhcp_agent'


class NeutronL3AgentRPCClient(NeutronRPCClient):
    service = 'l3_agent'


class NeutronMonitorAgentRPCClient(NeutronRPCClient):
    service = 'monitor_agent'


class NeutronOvsAgentRPCClient(NeutronRPCClient):
    service = 'q-agent-notifier-l2population-update'
