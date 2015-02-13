import os
import logging

from oslo.config import cfg
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

database_opts = [
    cfg.StrOpt('sql_connection',
               default='sqlite:///' +
               os.path.abspath(
                   os.path.join(os.path.dirname(__file__),
                                '../', 'sentry.sqlite')
               ),
               help="The SQLAlchemy connection string used to connect to the "
               "database",
               secret=False),
    cfg.BoolOpt("sql_debug", default=False,
                help="Whether echo raw sql in log."),
    cfg.IntOpt("sql_max_overflow", default=10,
               help='The SQLAlchemy max_overflow config'),
    cfg.IntOpt("sql_pool_size", default=5,
               help='The SQLAlchemy pool_size config'),
    cfg.IntOpt("sql_pool_recycle", default=3600,
               help='The SQLAlchemy pool_recycle config'),

]
CONF = cfg.CONF
CONF.register_opts(database_opts)


ENGINE = None
MAKER = None


def get_engine():
    global ENGINE
    if not ENGINE:
        if CONF.sql_debug:
            logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

        connection_dict = sqlalchemy.engine.url.make_url(CONF.sql_connection)

        if "sqlite" not in connection_dict.drivername:
            kwargs = dict(
                max_overflow=CONF.sql_max_overflow,
                pool_size=CONF.sql_pool_size,
                pool_recycle=CONF.sql_pool_recycle,
            )
        else:
            kwargs = dict()

        ENGINE = create_engine(CONF.sql_connection, **kwargs)
    return ENGINE


def enable_sql_debug():
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


def disable_sql_debug():
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARN)


def get_session():
    global MAKER
    if not MAKER:
        engine = get_engine()
        MAKER = sessionmaker(bind=engine, autocommit=True)

    return MAKER()
