import copy

from sentry.openstack.common import jsonutils
from sentry.db import mongo


class Event(object):
    """A normalization event object"""
    # instance uuid, network uuid, volume uuid...
    object_id = str()

    raw_id = str()
    token = str()
    is_admin = False
    request_id = str()
    roles = []
    project_id = str()
    project_name = str()
    user_name = str()
    user_id = str()
    event_type = str()
    message_id = str()
    payload = str()
    level = str()
    publisher_id = str()
    timestamp = str()
    remote_address = str()
    catalog = None

    # nova, cinder, glance
    service = str()
    # nova-api, cinder-volume
    binary = str()
    hostname = str()

    def to_dict(self):
        return dict((name, getattr(self, name)) for name in dir(self)
                    if not name.startswith('__') and
                    not callable(getattr(self, name)))


class Notification(object):
    """
    Mapper from raw json messages to python object
    """

    mapper = {
#        'id': "_id",
#        'token': "_context_auth_token",
#        'is_admin': "_context_is_admin",
#        'project_id': "_context_project_id",
#        'project_name': "_context_project_name",
#        'user_name': '_context_user_name',
#        'user_id': '_context_user_id',
#        'event_type': 'event_type',
#        'message_id': 'message_id',
#        'payload': 'payload',
#        'priority': 'priority',
#        'publisher_id': 'publisher_id',
#        'timestamp': 'timestamp',
#        'remote_address': '_context_remote_address',
#        'request_id': '_context_request_id',
#        'roles': "_context_roles",
#        'catelog': "_context_service_catalog",
#        'context_timestamp': '_context_timestamp',
#        'instance_id': 'payload.instance_id',
    }

    def __init__(self, json_body):
        if isinstance(json_body, basestring):
            json_body = jsonutils.loads(json_body)
        if isinstance(json_body, dict):
            pass
        else:
            raise ValueError("json_body should be a json string")

        self._verify(json_body)
        self.json_body = json_body

    def get(self, key, default_value=None):
        # parse nested string. eg. "payload.instance"
        if '.' in key:
            keys = key.split('.')

            x = self.json_body
            try:
                for k in keys:
                    x = x[k]
            except KeyError:
                x = None
            return x
        else:
            return self.json_body.get(key, default_value)

    def _verify(self, body):
        expected_key = ['priority', 'publisher_id', 'timestamp',
                        'event_type', 'message_id', 'payload']
        for key in expected_key:
            if key not in body:
                raise ValueError("Expect key %(key)s not in %(body)s" %
                                 {'key': key, 'body': body})

    def to_json(self, no_payload=False):
        new_body = copy.deepcopy(self.json_body)
        if no_payload:
            del new_body['payload']
        return new_body

    def to_dict(self, no_payload=True):
        obj = {}
        expected_attrs = ['id', 'token', 'project_id', 'project_name',
                          'user_id', 'user_name', 'event_type', 'message_id',
                          'priority', 'publisher_id', 'timestamp', 'roles',
                          'request_id', 'instance_id']

        for attr in expected_attrs:
            ori_key = self.mapper[attr]
            #FIXME
            if attr == 'id':
                # id attribute is a ObjectId('54924cb27c45f146bb57da6e')
                obj[attr] = str(self.get(ori_key))
            else:
                obj[attr] = self.get(ori_key)

        return obj

    @classmethod
    def find(cls, params, limit=-1):
        """
        params: dict
        """
        for key in params.keys():
            # Switch to new key
            value = params.pop(key)
            params[cls.mapper[key]] = value

        msgs = []
        for msg in mongo.raw_message_get_all(params):
            obj_msg = cls(msg)
            msgs.append(obj_msg.to_dict())
        return msgs
