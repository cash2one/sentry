#
# Created on 2013-1-21
#
# @author: hzyangtk@corp.netease.com
#

from sentry.common import http_communication
from sentry.openstack.common import cfg
from sentry.openstack.common import log


LOG = log.getLogger(__name__)
CONF = cfg.CONF

notify_configs = [
    cfg.BoolOpt('enable_platform_stop_alarm',
                default=False,
                help='Enable notify platform when vm state change'),
    cfg.StrOpt('stop_alarm_url_port',
               default='$url_port',
               help='Stop alarm url and port'),
    cfg.StrOpt('stop_alarm_request_uri',
               default=None,
               help='Stop alarm request uri.'),
    cfg.BoolOpt('enable_platform_binding',
                default=False,
                help='Enable notify platform binding when vm create'),
    cfg.StrOpt('alarm_binding_url_port',
               default='$url_port',
               help='Binding alarm url and port'),
    cfg.StrOpt('alarm_binding_request_uri',
               default=None,
               help='Binding alarm request uri.'),
]

CONF.register_opts(notify_configs)


def handle_before_alarm(message):
    """
    handle process before alarm
    include: notify cloud monitor to stop alarm when VM
             was deleted.
    """
    if CONF.enable_platform_stop_alarm:
        destroy_vm_notification = ['compute.instance.delete.end']
        if message.get('event_type') in destroy_vm_notification:
            _notify_platform_stop_alarm(message)
    if CONF.enable_platform_binding:
        create_vm_notification = ['compute.instance.create.end']
        if message.get('event_type') in create_vm_notification:
            _notify_platform_binding(message)


def _notify_platform_stop_alarm(message):
    """
    Notify platform to stop alarm when instance was deleted
    """
    LOG.debug(_("Begin notify platform stop alarm. Message is: %s") % message)
    url = CONF.stop_alarm_url_port
    request_uri = CONF.stop_alarm_request_uri
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    httpMethod = 'POST'
    project_id = message.get('payload').get('tenant_id')
    namespace = 'openstack'
    dimension = 'openstack=' + message.get('payload').get('instance_id')
    params_dict = {
                   'ProjectId': project_id,
                   'Namespace': namespace,
                   'Dimension': dimension
                   }
    send_notification = http_communication.HttpCommunication(url,
                        request_uri, headers, httpMethod, params_dict)
    response = send_notification.send_request_to_server()
    if response == None:
        LOG.warning(_("Notify platform binding error occurs"))
        return
    if response.status == 200:
        LOG.debug(_("Notify platform stop alarm success"))
    else:
        LOG.warning(_("Notify platform stop alarm failed, with response"
                      " status: %s") % response.status)


def _notify_platform_binding(message):
    """
    Notify platform to binding vm`s UUID to ip
    """
    LOG.debug(_("Begin notify platform binding. Message is: %s") % message)
    url = CONF.alarm_binding_url_port
    request_uri = CONF.alarm_binding_request_uri
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    httpMethod = 'POST'
    project_id = message.get('payload').get('tenant_id')
    namespace = 'openstack'
    dimension = 'openstack=' + message.get('payload').get('instance_id')
    instance_name = message.get('payload').get('display_name')
    try:
        fixed_ip = message['payload']['fixed_ips'][0]['address']
    except (KeyError, IndexError, TypeError):
        fixed_ip = '-'
    screen_name = instance_name + ": " + fixed_ip
    params_dict = {
                   'ProjectId': project_id,
                   'Namespace': namespace,
                   'Dimension': dimension,
                   'ScreenName': screen_name
                   }
    send_notification = http_communication.HttpCommunication(url,
                        request_uri, headers, httpMethod, params_dict)
    response = send_notification.send_request_to_server()
    if response == None:
        LOG.warning(_("Notify platform binding error occurs"))
        return
    if response.status == 200:
        LOG.debug(_("Notify platform binding success"))
    else:
        LOG.warning(_("Notify platform binding failed, with response"
                      " status: %s") % response.status)
