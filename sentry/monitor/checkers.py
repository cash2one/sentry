from sentry.monitor import state
from sentry.rpcclient import cinder
from sentry.rpcclient import neutron
from sentry.rpcclient import nova
from sentry.openstack.common import log as logging
from sentry.openstack.common.rpc import common as rpc_common

LOG = logging.getLogger(__name__)


class _AbstracChecker(object):
    """monitor.manager will use check to probe service's health

    The core method is check_status(), concrete class *should* implement it.
    """

    def __init__(self, hostname):
        """
        construct method accept only `hostname` as argument.
        """
        self.hostname = hostname

    def check_status(self):
        """
        Invoke a RPC to probe service's health.

        :returns: Please using the constant variable
                  `CHECK_OK`, `CHECK_FAILED`, `CHECK_TIMEOUT` as return value.
        """
        raise NotImplementedError('subclass should override check_status()')

    def __repr__(self):
        return '<%(class)s: %(host)s>' % {'class': self.__class__.__name__,
                                          'host': self.hostname}

    def __eq__(self, other):
        if type(other) is type(self):
            return self.hostname == other.hostname

    def __hash__(self):
        return hash(self.hostname) ^ hash(self.__class__.__name__)


class BaseChecker(_AbstracChecker):
    """Concrete checker who using RPCClient to invoke RPC to probe service."""

    # subclass should override this to correct RPCClient class
    rpc_client_cls = None

    # subclass should override this to correct rpc method to probe
    rpc_probe_method = None

    # subclass should override this to correct binary name
    binary_name = None

    def check_status(self):
        if not self.rpc_client_cls:
            raise ValueError('subclass must override "rpc_client_cls"')

        if not self.rpc_probe_method:
            raise ValueError('subclass must override "rpc_probe_method"')

        client = self._get_client()
        try:
            method = getattr(client, self.rpc_probe_method)
            method(self.hostname)
            # Even returns None, we think it ok.
            return state.CHECK_OK

        except rpc_common.Timeout:
            return state.CHECK_TIMEOUT

        except Exception as ex:
            LOG.exception(ex)
            return state.CHECK_FAILED

    def _get_client(self):
        if not hasattr(self, '_client'):
            # Cache client object
            self._client = self.rpc_client_cls()
        return self._client


#################
## nova checkers
#################

class NovaScheduler(BaseChecker):

    rpc_client_cls = nova.NovaSchedulerRPCClient
    rpc_probe_method = 'get_backdoor_port'
    binary_name = 'nova-scheduler'


class NovaCompute(BaseChecker):

    rpc_client_cls = nova.NovaComputeRPCClient
    rpc_probe_method = 'get_backdoor_port'
    binary_name = 'nova-compute'


class NovaConsoleauth(BaseChecker):

    rpc_client_cls = nova.NovaConsoleauthRPCClient
    rpc_probe_method = 'get_backdoor_port'
    binary_name = 'nova-consoleauth'


class NovaConductor(BaseChecker):

    rpc_client_cls = nova.NovaConductorRPCClient
    rpc_probe_method = 'get_backdoor_port'
    binary_name = 'nova-conductor'

##################
# cinder checkers
##################


class CinderScheduler(BaseChecker):

    rpc_client_cls = cinder.CinderSchedulerRPCClient
    rpc_probe_method = 'service_version'
    binary_name = 'cinder-scheduler'


class CinderVolume(BaseChecker):

    rpc_client_cls = cinder.CinderVolumeRPCClient
    rpc_probe_method = 'service_version'
    binary_name = 'cinder-volume'

##################
# neutron checkers
##################


class NeutronL3Agent(BaseChecker):

    rpc_client_cls = neutron.NeutronL3AgentRPCClient
    rpc_probe_method = 'ping'
    binary_name = 'neutron-l3-agent'


class NeutronDHCPAgent(BaseChecker):

    rpc_client_cls = neutron.NeutronDHCPAgentRPCClient
    rpc_probe_method = 'ping'
    binary_name = 'neutron-dhcp-agent'


class NeutronMonitorAgent(BaseChecker):

    rpc_client_cls = neutron.NeutronMonitorAgentRPCClient
    rpc_probe_method = 'ping'
    binary_name = 'neutron-monitor-agent'


class NeutronOvsAgent(BaseChecker):

    rpc_client_cls = neutron.NeutronOvsAgentRPCClient
    rpc_probe_method = 'ping'
    binary_name = 'neutron-ovs-agent'
