#
# Created on 2012-11-16
#
# @author: hzyangtk@corp.netease.com
#

from sentry.common import utils
from sentry.file_cache import alarm_content as alarm_content_list
from sentry.sender import handler
from sentry.sender import http_sender
from sentry.openstack.common import log
from oslo.config import cfg


CONF = cfg.CONF


sender_configs = [
    cfg.ListOpt('platform_project_id_list',
                    default=[],
                    help='Platform manager project ids'),
]


CONF.register_opts(sender_configs)
LOG = log.getLogger(__name__)
NEED_NOT_ALARM = ['RDS', 'DDB']
PLATFORM_MANAGER = ['platform_manager']
PRODUCT_MANAGER = ['product_manager']


def send_alarm(message):
    """
    The Message Example:
    {
        'message_id': str(uuid.uuid4()),
        'event_type': 'compute.create_instance',
        'publisher_id': 'compute.host1',
        'timestamp': timeutils.utcnow(),
        'priority': 'INFO',
        'payload': {'instance_id': 12, ... }
    }
    """
    format_data = _data_formater(message)
    if format_data is None:
        return
    LOG.info("After format data: %s" % str(format_data))
    alarm_owner = message.get('alarm_owner')
    if format_data['namespace'] in NEED_NOT_ALARM:
        LOG.info(_("This message need not alarm, with message: %s")
                 % str(message))
        return

    LOG.debug("Alarm owner: %s" % str(alarm_owner))
    for owner in alarm_owner:
        if owner in PRODUCT_MANAGER:
            http_sender.product_send_alarm(format_data)
        elif owner in PLATFORM_MANAGER:
            for project_id in CONF.platform_project_id_list:
                format_data['projectId'] = project_id
                http_sender.platform_send_alarm(format_data)


def _format_instance_offline(message, alarm_summary_content, alarm_contents):
    """
    Format instance offline alarm data.
    Data description of format_data:
    format_data: {
            "projectId":"",
            "namespace":"",
            "alarmType":"",
            "alarmTime":"",
            "alarmContent":"",
            "alarmContentSummary":"",
            "identifier":""
    }
    """
    instance_uuid = message['payload']['uuid']
    instance_ip = handler.get_instance_ip(instance_uuid)
    instance_name = message['payload']['display_name']
    project_id = message['payload']['project_id']
    namespace = 'openstack'
    alarm_type = 'InstanceOffLine'
    alarm_time = message['timestamp']
    alarm_content_summary = utils.join_string(
                        alarm_summary_content[alarm_type], instance_name,
                        ':', instance_uuid)
    alarm_content = utils.join_string(alarm_contents[alarm_type],
                              'name: ', instance_name,
                              ', uuid: ', instance_uuid,
                              ', ip: ', instance_ip,
                              ', project id: ', project_id)
    identifier = utils.join_string(instance_name, ':', instance_ip)

    return {
            "projectId": project_id,
            "namespace": namespace,
            "alarmType": alarm_type,
            "alarmTime": alarm_time,
            "alarmContent": alarm_content.encode('UTF-8'),
            "alarmContentSummary": alarm_content_summary.encode('UTF-8'),
            "identifier": identifier
    }


def _format_instance_error(message, alarm_summary_content, alarm_contents):
    message_payload = message['payload']
    instance_uuid = message_payload.get('instance_id', '')
    instance_ip = handler.get_instance_ip(instance_uuid)
    instance_name = message_payload.get('display_name', '')
    old_state = message_payload.get('old_state', '')
    if old_state is None:
        old_state = ''
    old_task_state = message_payload.get('old_task_state', '')
    if old_task_state is None:
        old_task_state = ''
    state_description = message_payload.get('state_description', '')
    if state_description is None:
        old_task_state = ''
    project_id = message_payload.get('tenant_id', '')
    namespace = 'openstack'
    alarm_type = 'InstanceError'
    alarm_time = message['timestamp']
    alarm_content_summary = utils.join_string(
                alarm_summary_content[alarm_type], instance_name,
                ':', instance_uuid)
    alarm_content = utils.join_string(alarm_contents[alarm_type],
                              'name: ', instance_name,
                              ', uuid: ', instance_uuid,
                              ', ip: ', instance_ip,
                              ', project id: ', project_id,
                              ', old_state: ', old_state,
                              ', old_task_state: ', old_task_state,
                              ', state description: ', state_description)
    identifier = utils.join_string(instance_name, ':', instance_ip)

    return {
            "projectId": project_id,
            "namespace": namespace,
            "alarmType": alarm_type,
            "alarmTime": alarm_time,
            "alarmContent": alarm_content.encode('UTF-8'),
            "alarmContentSummary": alarm_content_summary.encode('UTF-8'),
            "identifier": identifier
    }


def _format_nos_error(message, alarm_summary_content, alarm_contents):
    publisher_id = message.get('publisher_id', 'unknown')
    payload = message.get('payload', '')
    alarm_type = 'NosError'
    project_id = message.get('_context_project_id', 'unknown')
    namespace = 'openstack'
    alarm_time = message['timestamp']
    if message.get('event_type').startswith('glance'):
        service_name = utils.join_string('glance.', publisher_id)
        alarm_content = utils.join_string(alarm_contents[alarm_type],
                                          service_name, ', Detail: ', payload)
    else:
        service_name = publisher_id
        alarm_content = alarm_contents[alarm_type] + service_name
    alarm_content_summary = alarm_summary_content[alarm_type]
    identifier = service_name

    return {
            "projectId": project_id,
            "namespace": namespace,
            "alarmType": alarm_type,
            "alarmTime": alarm_time,
            "alarmContent": alarm_content.encode('UTF-8'),
            "alarmContentSummary": alarm_content_summary.encode('UTF-8'),
            "identifier": identifier
    }


def _format_nbs_error(message, alarm_summary_content, alarm_contents):
    service_name = message.get('publisher_id', 'unknown')
    project_id = message.get('_context_project_id', 'unknown')
    namespace = 'openstack'
    alarm_type = 'NbsError'
    alarm_time = message['timestamp']
    alarm_content_summary = alarm_summary_content[alarm_type]
    alarm_content = alarm_contents[alarm_type] + service_name
    identifier = service_name

    return {
            "projectId": project_id,
            "namespace": namespace,
            "alarmType": alarm_type,
            "alarmTime": alarm_time,
            "alarmContent": alarm_content.encode('UTF-8'),
            "alarmContentSummary": alarm_content_summary.encode('UTF-8'),
            "identifier": identifier
    }


def _format_unknown_error(message, alarm_summary_content, alarm_contents):
    service_name = message.get('publisher_id', 'unknown').split('.')[0]
    if 'metadata' in message['payload']:
        metadatas = message['payload']['metadata']
        namespace = 'openstack'
        for metadata in metadatas:
            if metadata['key'] == 'service':
                namespace = metadata['value']
        instance_uuid = message['payload']['instance_id']
        instance_ip = handler.get_instance_ip(instance_uuid)
        identifier = utils.join_string(message['payload']['display_name'],
                                       ':', instance_ip)
        project_id = message['payload']['tenant_id']
    else:
        instance_properties = \
                    message['payload']['request_spec']['instance_properties']
        namespace = instance_properties['metadata'].get('service', 'openstack')
        instance_uuid = message['payload']['request_spec']['instance_uuids'][0]
        instance_ip = handler.get_instance_ip(instance_uuid)
        identifier = utils.join_string(instance_properties['display_name'],
                                       ':', instance_ip)
        project_id = instance_properties['project_id']
    alarm_type = 'UnknownError'
    alarm_time = message['timestamp']
    alarm_content_summary = alarm_summary_content[alarm_type]
    alarm_content = utils.join_string(alarm_contents[alarm_type],
                                'service name: ', service_name,
                                ', event type: ', message['event_type'],
                                ', priority: ', message['priority'])

    return {
            "projectId": project_id,
            "namespace": namespace,
            "alarmType": alarm_type,
            "alarmTime": alarm_time,
            "alarmContent": alarm_content.encode('UTF-8'),
            "alarmContentSummary": alarm_content_summary.encode('UTF-8'),
            "identifier": identifier
    }


def _data_formater(message):
    """
    Now 5 alarms:
    "InstanceError",
    "NosError",
    "NbsError",
    "PlatformError",
    "InstanceOffLine",
    "UnknowError"

    Data description of format_data:
    format_data: {
            "projectId":"",
            "namespace":"",
            "alarmType":"",
            "alarmTime":"",
            "alarmContent":"",
            "alarmContentSummary":"",
            "identifier":""
    }
    """
    message = handler.set_alarm_timestamp(message)
    content = alarm_content_list.get_alarm_content()
    alarm_summary_content = content['alarm_summary_content']
    alarm_contents = content['alarm_content']

    LOG.debug("Alarm data: %s" % message)

    if handler.is_instance_down(message, content):
        # InstanceOffline: instance offline (heartbeat fail)
        return _format_instance_offline(message, alarm_summary_content,
                                        alarm_contents)
    elif handler.is_instance_state_error(message, content):
        # InstanceError: instance state to error
        return _format_instance_error(message, alarm_summary_content,
                                      alarm_contents)
    elif handler.is_nos_connection_failure(message, content):
        # NosError: NOS connection error
        return _format_nos_error(message, alarm_summary_content,
                                 alarm_contents)
    elif handler.is_nbs_connection_failure(message, content):
        # NbsError: NBS connection error
        return _format_nbs_error(message, alarm_summary_content,
                                 alarm_contents)
    elif handler.is_other_alarm(message, content):
        # UnknownError: other alarms
        return _format_unknown_error(message, alarm_summary_content,
                                     alarm_contents)
    else:
        LOG.info(_("Skip this alarm message, event_type is: %s")
                 % str(message.get('event_type')))
        return None
