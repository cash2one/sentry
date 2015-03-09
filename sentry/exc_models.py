class SentryPayload(object):
    """For easier access payload

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
                            '__builtins__': u"<module '__builtin__' (in)>",
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
    def __init__(self, payload_json):
        self.version = payload_json['_version_']
        self.datetime = payload_json['datetime']
        self.module = payload_json['module']
        self.levelno = payload_json['levelno']
        self.levelname = payload_json['levelname']
        self.name = payload_json['name']
        self.thread = payload_json['thread']
        self.process = payload_json['process']
        self.extra = payload_json.get('extra', {})
        self.func_name = payload_json['funcName']
        self.pathname = payload_json['pathname']
        self.binary_name = payload_json.get('binary')

        self.exc = SentryException(payload_json['exception'])

    @property
    def exc_class(self):
        return self.exc.exc_class

    @property
    def exc_value(self):
        return self.exc.exc_value

    @property
    def frames(self):
        return self.exc.frames

    @property
    def last_frame(self):
        try:
            return self.frames[-1]
        except IndexError:
            return None

    @property
    def exc_file_path(self):
        if self.last_frame:
            return self.last_frame.filename

    @property
    def exc_func_name(self):
        if self.last_frame:
            return self.last_frame.name

    @property
    def exc_lineno(self):
        if self.last_frame:
            return self.last_frame.lineno

    @property
    def has_exception(self):
        return bool(self.exc)


class SentryException(object):
    def __init__(self, payload):
        if not payload:
            self.exc_class = None
            self.exc_value = None
            self.frames = []
        else:
            self.exc_class = payload['exc_class']
            self.exc_value = payload['exc_value']
            self.frames = SentryFrame.from_list(payload['frames'])

    def __nonzero__(self):
        return not self.exc_class is None


class SentryFrame(object):

    def __init__(self, payload):
        self.context_line = payload['context_line']
        # It will be the absolute file path of the file
        self.filename = payload['filename']
        self.lineno = payload['lineno']
        self.local_vars = payload['local_vars']
        # the function name of the frame
        self.name = payload['name']

    @classmethod
    def from_list(cls, frame_list_json):
        objs = []
        for frame in frame_list_json:
            objs.append(cls(frame))
        return objs
