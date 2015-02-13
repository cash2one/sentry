from sentry.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class BaseAlarmDriver(object):
    """The basic alarm driver API, inherit from it."""

    def set_off(self, title, content):
        raise NotImplementedError()


class LogAlarmDriver(BaseAlarmDriver):
    """A Fake driver who only log off alarms."""

    def set_off(self, title, content):
        LOG.info('ALARM: \n'
                 '*** %(title)s ***\n'
                 '%(content)s\n' %
                 {'title': title, 'content': content})
