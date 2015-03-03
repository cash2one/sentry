from sqlalchemy.dialects import mysql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import object_mapper
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, DateTime, Boolean, Text, Index
from sqlalchemy import String, Integer, PickleType, LargeBinary

from sentry.openstack.common import jsonutils

BASE = declarative_base()


def MediumBlob():
    return LargeBinary().with_variant(mysql.MEDIUMBLOB(), 'mysql')


class MediumPickleType(PickleType):
    impl = MediumBlob()


class BaseModel(object):
    """Base class for models."""

    __table_initialized__ = False

    _json_fields = []
    _sortable_excludes = []
    _searchable_excludes = []

    # Each model should have field `id`
    id = Column(Integer, primary_key=True)

    @property
    def fields(self):
        return dict(object_mapper(self).columns).keys()

    @classmethod
    def get_fields(cls):
        return cls.metadata.tables[cls.__tablename__].columns.keys()

    @classmethod
    def _validate_field(cls, fields):
        all_fields = cls.get_fields()
        for f in fields:
            if f not in all_fields:
                raise ValueError('%s not field in %s' % (f, cls))

    @classmethod
    def get_sortable(cls):
        if hasattr(cls, '_sortable'):
            cls._validate_field(cls._sortable)
            return getattr(cls, '_sortable')
        else:
            excludes = getattr(cls, '_sortable_excludes', [])
            return set(cls.get_fields()) - set(excludes)

    @classmethod
    def get_searchable(cls):
        if hasattr(cls, '_searchable'):
            cls._validate_field(cls._searchable)
            return getattr(cls, '_searchable')
        else:
            excludes = getattr(cls, '_searchable_excludes', [])
            return set(cls.get_fields()) - set(excludes)

    def to_dict(self):
        json_fields = self._json_fields
        obj = {}
        for field in self.fields:
            attr = getattr(self, field)

            if field in json_fields:
                obj[field] = jsonutils.loads(attr)
            else:
                obj[field] = attr

        return obj


class Event(BASE, BaseModel):

    __tablename__ = 'events'
    __table_args__ = (
        Index('event_uname_obj_id_req_id_idx',
              'user_name', 'object_id', 'request_id', 'timestamp'),
        Index('event_obj_id_req_id',
              'object_id', 'request_id', 'timestamp'),
        Index('event_req_id',
              'request_id', 'timestamp'),
        Index('event_timestamp_idx',
              'timestamp'),
    )

    _sortable = ['timestamp', 'user_name', 'request_id']

    _searchable = ['timestamp',
                   'user_name',
                   'object_id',
                   'request_id']
    _json_fields = ['roles', 'payload']

    object_id = Column(String(100))
    message_id = Column(String(100))
    raw_message_id = Column(Integer, ForeignKey('raw_messages.id'))
    raw_message = relationship('RawMessage', backref="event", uselist=False)
    token = Column(String(100))
    is_admin = Column(Boolean, default=False)
    request_id = Column(String(100))
    # list
    roles = Column(String(100))
    project_id = Column(String(100))
    project_name = Column(String(100))
    user_name = Column(String(100))
    user_id = Column(String(100))
    event_type = Column(String(100))
    payload = Column(Text())
    level = Column(String(20))
    remote_address = Column(String(20))
    publisher_id = Column(String(100))
    timestamp = Column(DateTime())
    hostname = Column(String(50))
    binary = Column(String(20))
    # e.g. nova, cinder, glance
    service = Column(String(20))


class RawMessage(BASE, BaseModel):

    __tablename__ = 'raw_messages'
    __table_args__ = ()

    id = Column(Integer, primary_key=True)
    json = Column(Text, nullable=False)


class ErrorLog(BASE, BaseModel):

    __tablename__ = 'error_logs'
    __table_args__ = (
        Index('datetime_x_hostname', 'datetime', 'hostname'),
    )

    datetime = Column(DateTime())
    hostname = Column(String(255))
    payload = Column(MediumPickleType(), default={})
    stats_id = Column(Integer, ForeignKey('error_log_stats.id'))

    @property
    def count(self):
        return self.error_stats.count

    @property
    def title(self):
        return self.error_stats.title

    @property
    def log_level(self):
        return self.error_stats.log_level

    @property
    def on_process(self):
        return self.error_stats.on_process

    @property
    def stats_uuid(self):
        return self.error_stats.uuid

    @property
    def sentry_payload(self):
        return SentryPayload(self.payload)

    def __repr__(self):
        return ('<ErrorLog> %(datetime)s at %(hostname)s' %
                {'datetime': self.datetime, 'hostname': self.hostname})


class SentryPayload(object):
    """For easier access payload"""
    def __init__(self, payload_json):
        self.version = payload_json['_version_']
        self.datetime = payload_json['datetime']
        self.levelno = payload_json['levelno']
        self.levelname = payload_json['levelname']
        self.name = payload_json['name']
        self.thread = payload_json['thread']
        self.process = payload_json['process']
        self.extra = payload_json.get('extra', {})
        self.func_name = payload_json['funcName']
        self.pathname = payload_json['pathname']
        self.binary_name = payload_json.get('binary')

        self.exception = SentryException(payload_json['exception'])


class SentryException(object):
    def __init__(self, payload):
        if not payload:
            self.exc_class = None
            self.exc_value = None
            self.frames = []
        else:
            self.exc_class = payload['exc_class']
            self.exc_value = payload['exc_value']
            self.frames = SentryFrame.hybird(payload['frames'])


class SentryFrame(object):
    def __init__(self, payload):
        self.context_line = payload['context_line']
        self.filename = payload['filename']
        self.lineno = payload['lineno']
        self.local_vars = payload['local_vars']
        self.name = payload['name']

    @classmethod
    def hybird(cls, frame_list_json):
        objs = []
        for frame in frame_list_json:
            objs.append(cls(frame))
        return objs


class ErrorLogStats(BASE, BaseModel):

    __tablename__ = 'error_log_stats'
    __table_args__ = (
        Index('title_x_loglevel_x_count_on_process',
              'title', 'log_level', 'count', 'on_process'),
        Index('id_x_uuid',
              'uuid', 'id'),
    )

    _searchable = ['uuid', 'title', 'log_level', 'on_process']
    _sortable = ['title', 'log_level', 'datetime', 'count', 'on_process']

    uuid = Column(String(36))
    title = Column(String(255))
    log_level = Column(String(10))
    datetime = Column(DateTime())
    count = Column(Integer)
    on_process = Column(Boolean, default=False)
    errors = relationship("ErrorLog", backref="error_stats")

    def __repr__(self):
        return ('<ErrorLogStats> %(title)s at %(level)s, count: %(count)s' %
                {'title': self.title, 'level': self.log_level,
                 'count': self.count})
