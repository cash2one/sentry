from sqlalchemy.dialects import mysql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import object_mapper
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, DateTime, Boolean, Text, Index
from sqlalchemy import String, Integer, PickleType, LargeBinary

from sentry import exc_models
from sentry.openstack.common import jsonutils
from sentry.openstack.common import timeutils

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

# -----------------------------
# exception info tables
# -----------------------------


class ExcInfo(BASE, BaseModel):

    __tablename__ = 'exc_info'
    __table_args__ = (
        Index('exc_info_uuid_idx',
              'uuid'),
        Index('exc_info_count_idx',
              'count'),
        Index('exc_info_binary_idx',
              'binary'),
        Index('exc_info_idx',
              'exc_class', 'file_path', 'func_name', 'lineno'),
    )

    last_time = Column(DateTime())
    binary = Column(String(36))
    count = Column(Integer)
    on_process = Column(Boolean, default=False)
    uuid = Column(String(36))
    exc_class = Column(String(255))
    file_path = Column(String(1024))
    func_name = Column(String(255))
    lineno = Column(Integer)

    def __repr__(self):
        return ('<ExcInfo: %(exc_cls)s, count: %(count)s>' %
                {'exc_cls': self.exc_class, 'count': self.count})


class ExcInfoDetail(BASE, BaseModel):

    __tablename__ = 'exc_info_detail'
    __table_args__ = (
        Index('exc_info_created_at_hostname',
              'created_at', 'hostname'),
    )

    created_at = Column(DateTime())
    hostname = Column(String(255))
    exc_value = Column(String(1024))
    payload = Column(MediumPickleType(), default={})
    exc_info_id = Column(Integer, ForeignKey('exc_info.id'))
    exc_info = relationship('ExcInfo', backref='details')

    @property
    def count(self):
        return self.exc_info.count

    @property
    def exc_class(self):
        return self.exc_info.exc_class

    @property
    def binary(self):
        return self.exc_info.binary

    @property
    def on_process(self):
        return self.exc_info.on_process

    @property
    def uuid(self):
        return self.exc_info.uuid

    @property
    def file_name(self):
        return self.exc_info.file_name

    @property
    def func_name(self):
        return self.exc_info.func_name

    @property
    def lineno(self):
        return self.exc_info.lineno

    @property
    def spayload(self):
        return exc_models.SentryPayload(self.payload)

    @property
    def frames(self):
        return self.spayload.frames

    def __repr__(self):
        return ('<ExcInfoDetail: %(datetime)s at %(hostname)s>' %
                {'datetime': self.created_at, 'hostname': self.hostname})


class Config(BASE, BaseModel):

    __tablename__ = 'configs'
    __table_args__ = (
        Index('id_x_key',
              'id', 'key'),
        Index('created_at_x_updated_at',
              'created_at', 'updated_at'),
    )

    key = Column(String(255))
    value = Column(PickleType(), default=None)
    created_at = Column(DateTime(), default=timeutils.utcnow)
    updated_at = Column(DateTime(), default=timeutils.utcnow)

    def __repr__(self):
        return '<Config %s = %s>' % (self.key, self.value)
