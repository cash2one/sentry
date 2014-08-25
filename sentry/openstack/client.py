import json

from sentry.common import client
from sentry.common import utils
from oslo.config import cfg
import sentry.openstack.common.log as logging

LOG = logging.getLogger(__name__)

NOVA_OPTS = [
    cfg.StrOpt("nova_host", default="0.0.0.0"),
    cfg.IntOpt("nova_port", default=8774),
    cfg.StrOpt("nova_version", default="/v2")
]

CONF = cfg.CONF
CONF.register_opts(NOVA_OPTS)


class BaseClient(client.BaseClient):
    """client base class for make request of other module"""

    def request(self, req):
        return self.send_request(req.method, req.path,
                                 params=req.params.mixed(),
                                 headers=req.headers, body=req.body)

    def send_request(self, method, action, params={}, headers={}, body=None):
        LOG.debug(_("%(method)s %(action)s %(params)s %(headers)s"),
                                locals())
        res = self.do_request(method, action, params=params, headers=headers,
                              body=body)
        data = json.loads(res.read())
        LOG.debug(_("response for %s %s successfully with %.100s... in body") %
                    (method, action, data))
        return data, res.getheaders()


class KeystoneAdminClient(BaseClient):

    def __init__(self, auth_tok=None, creds=None):
        host = CONF.keystone_host
        admin_port = CONF.keystone_admin_port
        doc_root = CONF.keystone_version
        super(KeystoneAdminClient, self).__init__(host=host, port=admin_port,
                doc_root=doc_root, auth_tok=auth_tok, creds=creds)


class KeystonePublicClient(BaseClient):

    def __init__(self, auth_tok=None, creds=None):
        host = CONF.keystone_host
        admin_port = CONF.keystone_public_port
        doc_root = CONF.keystone_version
        super(KeystonePublicClient, self).__init__(host=host, port=admin_port,
                doc_root=doc_root, auth_tok=auth_tok, creds=creds)


class NovaClient(BaseClient):

    def __init__(self, auth_tok=None, creds=None):
        host = CONF.nova_host
        admin_port = CONF.nova_port
        doc_root = CONF.nova_version
        super(NovaClient, self).__init__(host=host, port=admin_port,
                doc_root=doc_root, auth_tok=auth_tok, creds=creds)
