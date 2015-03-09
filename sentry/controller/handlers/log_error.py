from oslo.config import cfg

from sentry import exc_models
from sentry.db import api as dbapi
from sentry.alarm import api as alarmapi
from sentry.openstack.common import log as logging


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class Handler(object):

    def __init__(self):
        self.alarm = alarmapi.AlarmAPI()

    def handle_message(self, message):
        if not self.can_handle(message):
            return
        self._handle(message)

    def can_handle(self, message):
        msg_type = message.get('event_type')

        if msg_type and msg_type == 'sentry.log.error':
            return True
        else:
            LOG.warn("Unknown msg_type %s, can not process." % msg_type)
            return False

    def _handle(self, message):
        hostname = message.get('publisher_id')
        payload = message.get('payload', {})

        spayload = exc_models.SentryPayload(message.get('payload', {}))

        if not spayload.has_exception:
            LOG.debug("no exception log, skip.")
            return

        binary = spayload.binary_name
        exc_class = spayload.exc_class
        exc_value = spayload.exc_value
        file_path = spayload.exc_file_path
        func_name = spayload.exc_func_name
        lineno = spayload.exc_lineno
        created_at = spayload.datetime

        LOG.info("Receive exception: '%(exc_value)s' from: %(hostname)s" %
                 {'exc_value': exc_value, 'hostname': hostname})

        exc_info_detail = dbapi.exc_info_detail_create(
            hostname, payload, binary, exc_class, exc_value, file_path,
            func_name, lineno, created_at
        )

        self.alarm.alarm_exception(exc_info_detail)
