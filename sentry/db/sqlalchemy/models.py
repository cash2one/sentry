from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, DateTime, Boolean, Text, Index
from sqlalchemy import String, Integer

BASE = declarative_base()


class Event(BASE):

    __tablename__ = 'events'
    __table_args__ = (
        Index('event_message_id', 'message_id'),
        Index('project_name_x_user_name_idx',
              'project_name', 'user_name'),
        Index('project_id_x_user_id_idx',
              'project_id', 'user_id'),
        Index('request_id', 'request_id'),
    )

    id = Column(Integer, primary_key=True)
    message_id = Column(String(100))
    token = Column(String(100), nullable=False)
    raw_message = Column(Integer, ForeignKey('raw_messages.id'))
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
    publisher_id = Column(String(100))
    timestamp = Column(DateTime())
    hostname = Column(String(50))
    binary = Column(String(20))
    # e.g. nova, cinder, glance
    service = Column(String(20))


class RawMessage(BASE):

    __tablename__ = 'raw_messages'
    __table_args__ = ()

    id = Column(Integer, primary_key=True)
    json = Column(Text, nullable=False)
