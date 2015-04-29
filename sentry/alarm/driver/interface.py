from sentry.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class BaseAlarmDriver(object):
    """The basic alarm driver API, inherit from it."""

    def set_off(self, title, content, **headers):
        raise NotImplementedError()
