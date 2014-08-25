#
# Created on 2012-12-4
#
# @author: hzyangtk@corp.netease.com
#

from sentry.common import exception
from oslo.config import cfg
from sentry.openstack.common import log as logging
from novaclient.v1_1.client import Client


LOG = logging.getLogger(__name__)
FLAGS = cfg.CONF


nova_client_configs = [
    cfg.StrOpt('novaclient_username',
                default='default',
                help='Nova Client Username'),
    cfg.StrOpt('novaclient_password',
                default='default',
                help='Nova Client Password'),
    cfg.StrOpt('novaclient_projectName',
                default='default',
                help='Nova Client Project Name'),
    cfg.StrOpt('novaclient_keystoneUrl',
                default='default',
                help='Nova Client Keystone Url'),
]

FLAGS.register_opts(nova_client_configs)


class CallNovaClient(object):
    '''
        Connect to nova client, and get instances and flavors
    '''
    def __init__(self):
        '''
            Get nova client object by admin user.
        '''
        try:
            self.nova_client = Client(FLAGS.novaclient_username,
                                      FLAGS.novaclient_password,
                                      FLAGS.novaclient_projectName,
                                      FLAGS.novaclient_keystoneUrl,
                                      service_type='compute')
        except Exception:
            LOG.exception(_("Error during get nova client exception. Maybe "
                            "cause of error auth for keystone"))
            self.nova_client = None

    def get_all_instances(self):
        '''
            Get all instances obeject in different hosts by nova client
        '''
        try:
            if self.nova_client is None:
                raise Exception()
            detailed = True
            search_opts = {'all_tenants': 'True'}
            instances = self.nova_client.servers.list(detailed, search_opts)
            return instances
        except Exception:
            msg = (_("Error during get all instances from nova client"
                     " api error, maybe the connection error"))
            LOG.exception(msg)
            raise exception.NovaclientHelperException(msg)

    def get_instance_by_UUID(self, instance_id):
        '''
            Get instance object with UUID by nova client call
        '''
        try:
            if self.nova_client is None:
                raise Exception()
            instance = self.nova_client.servers.get(instance_id)
            return instance
        except Exception:
            msg = (_("Error during get specified instance from "
                     "novaclient api error. uuid %(instance_id)s."), locals())
            LOG.exception(msg)
            raise exception.NovaclientHelperException(msg)

    def get_flavors(self, flavorId):
        '''
            Get flavors datas by nova client
        '''
        try:
            if self.nova_client is None:
                raise Exception()
            flavors = self.nova_client.flavors.get(flavorId)
            return flavors
        except Exception:
            msg = (_("Error during get flavors from novaclient api "
                     "error, check the api connection and flavor value."
                     " Flavor id is: %(flavorId)s."), locals())
            LOG.exception(msg)
            raise exception.NovaclientHelperException(msg)
