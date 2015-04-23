from sentry.rpcclient import base
from sentry import messaging


__all__ = ['CinderSchedulerRPCClient',
           'CinderVolumeRPCClient']


class CinderRPCClient(base.BaseRPCClient):

    exchange = 'openstack'
    version = '1.0'

    def __init__(self):
        self.bus = messaging.cinder_bus()

    def _topic(self, host):
        return '%s:%s' % (self.service, host)

    def service_version(self, host):
        topic = self._topic(host)
        return self._call_bus(topic, 'service_version')


class CinderSchedulerRPCClient(CinderRPCClient):
    service = 'cinder-scheduler'


class CinderVolumeRPCClient(CinderRPCClient):
    service = 'cinder-volume'
