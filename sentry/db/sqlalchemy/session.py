import os
import logging

from oslo.config import cfg
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
                help="Whether echo raw sql in log.")

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

        kwargs = dict(
            echo=CONF.sql_debug,
        )

        ENGINE = create_engine(CONF.sql_connection, **kwargs)
    return ENGINE


def get_session():
    global MAKER
    if not MAKER:
        engine = get_engine()
        MAKER = sessionmaker(bind=engine)

    return MAKER()
