class BaseModel(object):
    def to_dict(self):
        return dict((name, getattr(self, name)) for name in dir(self)
                    if not name.startswith('__') and
                    not callable(getattr(self, name)))


class Event(BaseModel):
    """A normalization event object"""
    # instance uuid, network uuid, volume uuid...
    object_id = str()

    raw_json = str()
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


class ErrorLog(BaseModel):

    title = str()
    log_level = str()
    datetime = str()
    hostname = str()
    payload = dict()
