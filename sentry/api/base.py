#
# Created on 2012-12-3
#
# @author: hzyangtk@corp.netease.com
#

import copy
import json

import webob

from sentry.file_cache import setting_list
from sentry.openstack import client
from sentry.openstack.common import log as logging


LOG = logging.getLogger(__name__)


def _encode_list_content(data_list, encoding='UTF-8'):
    for data in data_list:
        for key, value in data.items():
            data.pop(key)
            key = key.encode(encoding)
            value = value.encode(encoding)
            data[key] = value


def get_product_metric_list(req):
    """Return product metric list of sentry and monitor"""
    settings = setting_list.get_setting_list()
    metric_list = copy.deepcopy(settings.get('product_metric_list', []))
    _encode_list_content(metric_list)
    return json.dumps(metric_list, ensure_ascii=False)


def get_platform_metric_list(req):
    """Return platform metric list of sentry and monitor"""
    list_name = None
    if req.params.get('DimensionName') == 'Platform':
        list_name = 'platform_NVSPlatform_metric_list'
    elif req.params.get('DimensionName') == 'host':
        list_name = 'platform_host_metric_list'
    else:
        raise webob.exc.HTTPBadRequest()

    settings = setting_list.get_setting_list()
    metric_list = copy.deepcopy(settings.get(list_name, []))
    _encode_list_content(metric_list)
    return json.dumps(metric_list, ensure_ascii=False)


def get_product_alarm_event_list(req):
    """Return product alarm event list of sentry"""
    settings = setting_list.get_setting_list()
    alarm_event_list = copy.deepcopy(settings.get('product_alarm_event_list',
                                                  []))
    _encode_list_content(alarm_event_list)
    return json.dumps(alarm_event_list, ensure_ascii=False)


def get_platform_alarm_event_list(req):
    """Return platform alarm event list of sentry"""
    settings = setting_list.get_setting_list()
    alarm_event_list = copy.deepcopy(settings.get('platform_alarm_event_list',
                                                  []))
    _encode_list_content(alarm_event_list)
    return json.dumps(alarm_event_list, ensure_ascii=False)


def get_product_instance_list(req):
    """Return product instance list of sentry"""
    tenant_id = req.params.get('ProjectId', None)
    if tenant_id is None:
        msg = _("project id invalid")
        raise webob.exc.HTTPBadRequest(explanation=msg)
    token = req.headers.get('x-auth-token', None)
    if token is None:
        msg = _("token is invalid")
        raise webob.exc.HTTPForbidden(explanation=msg)

    # NOTE(hzyangtk): call nova client to get isntance list
    method = 'GET'
    path = '/%s/servers/detail' % tenant_id
    params = {'tenant_id': tenant_id}
    nova_client = client.NovaClient(token)
    result, headers = nova_client.send_request(
                            method, path, params, headers={})

    res_instances = []
    instances = result.get('servers')
    if instances:
        for instance in instances:
            ip_addrs = instance.get('addresses')
            name = instance.get('name')
            ip_v4 = None
            if ip_addrs:
                try:
                    ip_v4 = ip_addrs.get('private')[0].get('addr')
                except (KeyError, IndexError, TypeError):
                    LOG.exception(_("Get ip address error with uuid: %s")
                                  % instance.get('id'))
            if ip_v4 == None:
                LOG.warning(_("instance ip not found with uuid: %s")
                            % instance.get('id'))
                continue
            res_instances.append("%(name)s:%(ip)s" % {'name': name,
                                                      'ip': ip_v4})
    return json.dumps(res_instances)


def get_platform_instance_list(req):
    """Return platform users/hosts/platforms list of sentry"""
    tenant_id = req.params.get('ProjectId', None)
    if tenant_id is None:
        msg = _("project id invalid")
        raise webob.exc.HTTPBadRequest(explanation=msg)
    token = req.headers.get('x-auth-token', None)
    if token is None:
        msg = _("token is invalid")
        raise webob.exc.HTTPForbidden(explanation=msg)

    result = []

    dimension_name = req.params.get('DimensionName')
    if dimension_name == 'host':
        result = _get_platform_host_list(tenant_id, token)
    elif dimension_name == 'Platform':
        result.append('NVSPlatform')
    elif dimension_name == 'AZ':
        result = _get_platform_AZ_list(tenant_id, token)
    else:
        raise webob.exc.HTTPBadRequest()

    return json.dumps(result)


def _get_platform_host_list(tenant_id, token):
    """Return all the host list"""
    method = 'GET'
    path = '/%s/os-hosts' % tenant_id
    params = {}
    nova_client = client.NovaClient(token)
    result, headers = nova_client.send_request(
                            method, path, params, headers={})
    hosts = result.get('hosts')
    if hosts is None:
        msg = _("host not found")
        raise webob.exc.HTTPNotFound(explanation=msg)
    host_set = set()
    host_list = list()
    for host in hosts:
        host_name = host.get('host_name')
        if host_name not in host_set:
            host_set.add(host_name)
            host_list.append({
                'id': host_name,
                'screenName': host_name
            })
    return host_list


def _get_platform_AZ_list(tenant_id, token):
    """Return all the AZ list"""
    method = 'GET'
    path = '/%s/availability-zones' % tenant_id
    params = {}
    nova_client = client.NovaClient(token)
    result, headers = nova_client.send_request(
                            method, path, params, headers={})
    availability_zones = result.get('availability_zones')
    if availability_zones is None:
        msg = _("availability zone not found")
        raise webob.exc.HTTPNotFound(explanation=msg)
    az_list = list()
    for az in availability_zones:
        if az.get('zoneState') == 'available':
            az_info = {
                'id': az.get('zoneName'),
                'screenName': az.get('zoneName')
            }
            az_list.append(az_info)
    return az_list
