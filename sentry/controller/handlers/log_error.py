from oslo.config import cfg

from sentry.db import models
from sentry.db import api as dbapi
from sentry.alarm import api as alarmapi
from sentry.openstack.common import log as logging


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


"""
The example of sentry.log.error message:

{
    '_context_request_id': 'req-e0546a6a-bfba-4729-b1e2-43eeaad5b16d',
    'event_type': 'sentry.log.error',
    'timestamp': '2015-02-2806: 26: 01.134761',
    '_context_auth_token': None,
    '_context_show_deleted': False,
    '_context_tenant': None,
    'payload': {
        'project': 'nova',
        'binary': 'nova-api-os-compute',
        'exception': {
            'frames': [
                {
                    'name': '<module>',
                    'local_vars': {
                        '__builtins__': u"<module '__builtin__' (built-in)>",
                        '__file__': u"'/usr/local/bin/nova-api'",
                        '__package__': 'None',
                        'sys': u"<module 'sys' (built-in)>",
                        '__name__': u"'__main__'",
                        'main': '<functionmainat0x7f7130efdc80>',
                        '__doc__': 'None'
                    },
                    'lineno': 10,
                    'context_line': 'sys.exit(main())',
                    'filename': '/usr/local/bin/nova-api'
                },
                {
                    'name': 'main',
                    'local_vars': {
                        'launcher': 'ssLauncherobjectat0x7f7130f1ded0>',
                        'api': u"'osapi_compute'",
                        'should_use_ssl': 'False'
                    },
                    'lineno': 51,
                    'context_line': 'server=service.WSGIService(api,
                    use_ssl=should_use_ssl)',
                    'filename': '/opt/stack/nova/nova/cmd/api.py'
                },

            ],
            'exc_class': u"<class 'socket.error'>",
            'exc_value': '[Errno98]Addressalreadyinuse'
        },
        'threadName': 'MainThread',
        'name': 'nova',
        'thread': 140124231193616,
        'extra': {
            'project': 'nova',
            'instance': '',
            'version': 'unknown'
        },
        'process': 17668,
        'funcName': 'logging_excepthook',
        'args': [

        ],
        'module': 'log',
        'datetime': '2015-02-28T06: 26: 01.131970',
        'levelno': 50,
        'processName': 'MainProcess',
        'pathname': '/opt/stack/nova/nova/openstack/common/log.py',
        'msecs': 131.96992874145508,
        'relativeCreated': 2175.8458614349365,
        '_version_': '0.1',
        'message': '[Errno98]Addressalreadyinuse',
        'filename': 'log.py',
        'levelname': 'CRITICAL',
        'msg': '[Errno98] Address already in use'
    },
    '_unique_id': '60d621fba9b24521b0df9319d3305216',
    '_context_is_admin': True,
    '_context_read_only': False,
    '_context_user': None,
    'publisher_id': 'jenkins-devstack-13',
    'message_id': '81f636a0-ec5d-43c9-9968-aec4457e7fd3',
    'priority': 'CRITICAL'
}
"""


class Handler(object):

    def __init__(self):
        self.alarm = alarmapi.AlarmAPI()

    def can_handle(self, message):
        msg_type = message.get('event_type')

        if msg_type and msg_type == 'sentry.log.error':
            return True
        else:
            return False

    def handle_message(self, message):
        if not self.can_handle(message):
            return

        errorlog = models.ErrorLog()
        errorlog.hostname = message.get('publisher_id')

        payload = message.get('payload', {})
        errorlog.title = payload.get('message') or payload.get('msg')
        errorlog.log_level = payload.get('levelname').lower()
        errorlog.datetime = payload.get('datetime')
        errorlog.payload = payload

        if errorlog.title and len(errorlog.title) > 255:
            LOG.warn("Error log's title was too long, ignore it.")
            return

        LOG.info("Receive an error: %(title)s from %(hostname)s" %
                 {'title': errorlog.title, 'hostname': errorlog.hostname})
        db_error_log = dbapi.error_log_create(errorlog)

        self.alarm.alarm_error_log(db_error_log)
