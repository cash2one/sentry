"""
A rabbitMQ client based on kombu. With connection pool, and reconnection
build in.
"""

from contextlib import contextmanager

import eventlet
from eventlet import pools
import kombu
from kombu import entity
from kombu import connection

from sentry.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class RabbitClient(object):

    def __init__(self, hostname='localhost', userid='guest', password='guest',
                 virtual_host='/', port='5672'):
        conf = {
            'hostname': hostname,
            'userid': userid,
            'password': password,
            'virtual_host': virtual_host,
            'port': port,
        }
        self.pool = Pool(conf, Connection)

    @contextmanager
    def get_connection(self):
        conn = self.pool.get()
        try:
            yield conn
        finally:
            self.pool.put(conn)

    def _acquire_connection(self):
        return self.pool.get()

    def _put_connection(self, conn):
        self.pool.put(conn)

    def fanout(self, exchange_name, msg, durable=False, ttl=None):
        """
        :param exchange_name: string, represent the exchange name, the
                              exchange type will be `fanout`.
        :param msg: dict, the content of message
        :param durable: boolean, whether make a durable message.
        :param ttl: int, expiration of message in milliseconds.
        """
        conn = self._acquire_connection()

        while True:
            try:
                channel = conn.get_channel()
                exchange = entity.Exchange(name=exchange_name, type='fanout',
                                        channel=channel, durable=durable)
                exchange.declare()

                # RabbitMQ support below properites:
                #
                #   content_type
                #   content_encoding
                #   priority
                #   correlation_id
                #   reply_to
                #   expiration
                #   message_id
                #   timestamp
                #   type
                #   user_id
                #   app_id
                #   cluster_id
                properties = {}

                if ttl:
                    properties['expiration'] = str(ttl)

                producer = kombu.Producer(channel, exchange=exchange)
                producer.publish(msg, **properties)

                break
            except Exception:
                LOG.exception("Retry..")
                eventlet.sleep(1)
                conn.make_sure_connected()

        self._put_connection(conn)


class Connection(object):

    def __init__(self, conf):
        self.conf = conf
        conn_kwargs = {
            'hostname': self.conf['hostname'],
            'userid': self.conf['userid'],
            'password': self.conf['password'],
            'virtual_host': self.conf['virtual_host'],
            'port': self.conf['port'],
            'transport': self.conf.get('transport', 'amqplib'),
        }
        self.connection = connection.Connection(**conn_kwargs)
        self.make_sure_connected()

    def get_channel(self):
        return self.connection.channel()

    def make_sure_connected(self):
        while True:
            try:
                self.reconnect()
                break
            except Exception:
                LOG.exception("Connection to rabbitmq server failed, retry")
                eventlet.sleep(1)

    def reconnect(self):
        self.connection.release()
        self.connection.connect()

    def close(self):
        self.connection.release()


class Pool(pools.Pool):
    """Class that implements a Pool of Connections."""
    def __init__(self, conf, connection_cls, *args, **kwargs):
        self.connection_cls = connection_cls
        self.conf = conf
        kwargs.setdefault("max_size", 30)
        kwargs.setdefault("order_as_stack", True)
        super(Pool, self).__init__(*args, **kwargs)

    def create(self):
        LOG.debug('Pool creating new connection')
        return self.connection_cls(self.conf)

    def empty(self):
        while self.free_items:
            self.get().close()
        # Force a new connection pool to be created.
        # Note that this was added due to failing unit test cases. The issue
        # is the above "while loop" gets all the cached connections from the
        # pool and closes them, but never returns them to the pool, a pool
        # leak. The unit tests hang waiting for an item to be returned to the
        # pool. The unit tests get here via the tearDown() method. In the run
        # time code, it gets here via cleanup() and only appears in service.py
        # just before doing a sys.exit(), so cleanup() only happens once and
        # the leakage is not a problem.
        self.connection_cls.pool = None
