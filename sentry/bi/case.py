# -*- coding: utf8 -*-
import inspect
from sentry.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class TaggerError(Exception):
    """Common Exception raised when tag() failed."""
    pass


class Tagger(object):
    """An abstract class for tagger.

    Tagger is instereted in an event_type, when `BIAnalyzer` found
    a notification match the event_type, `BIAnalyzer` will using this
    tagger to tag the `action` object.

    tag() means fill the attributes of action. e.g. start_at, end_at,
    tenant_id .etc .
    """
    event_type = None

    def __init__(self):
        if self.event_type is None:
            raise ValueError('subclass must define `event_type`')

    def process(self, action, message):
        """Start point of every request. `BIAnalyzer` will calling this method
        when a notification arrived.
        """
        try:
            self.check_event_type(message)
            self.tag(action, message)
        except TaggerError:
            pass

    def tag(self, action, message):
        """will side-affect on `action`, fill action's fields from messsage"""
        raise NotImplementedError("Subclass should implement tag()")

    def check_event_type(self, message):
        event_type = message['event_type'].strip()
        if event_type != self.event_type:
            raise TaggerError('event_type %s not match %s' %
                              (event_type, self.event_type))

    def fill_request_id_start_at_tenant_name_and_id(self, action, message):
        action.request_id = message.get('_context_request_id')
        action.start_at = message.get('timestamp')
        action.tenant_name = message.get('_context_project_name')
        action.tenant_id = message.get('_context_project_id')

    def fill_end_at(self, action, message):
        if action.start_at is None:
            msg = ("%s: %s not start but ending" % (self, action))
            LOG.warn(msg)
            return

        action.end_at = message.get('timestamp')

    def fill_bi_name(self, action, name):
        if action.bi_name is not None:
            msg = ('duplicatly setting bi_name. %(old)s => %(new)s' %
                   {'old': action.bi_name, 'new': name})
            raise TaggerError(msg)
        action.bi_name = name

    def __repr__(self):
        return self.event_type


class _CommonEndTagger(Tagger):
    """EndTagger just fill 'end_at' attribute of action"""

    def tag(self, action, message):
        self.fill_end_at(action, message)


class _CommonStartTagger(Tagger):
    """StartTagger calling subclass _get_bi_name to get real bi_name."""

    def tag(self, action, message):
        self.fill_request_id_start_at_tenant_name_and_id(action, message)

        bi_name = self._get_bi_name(message)
        self.fill_bi_name(action, bi_name)

    def _get_bi_name(self, message):
        raise NotImplementedError('subclass must implement `_get_bi_name`')


class _SyncTagger(Tagger):
    """SyncTagger fill start_at and end_at at the same time."""

    def tag(self, action, message):
        self.fill_request_id_start_at_tenant_name_and_id(action, message)
        bi_name = self._get_bi_name(message)
        self.fill_bi_name(action, bi_name)
        self.fill_end_at(action, message)

    def _get_bi_name(self, message):
        raise NotImplementedError('subclass must implement `_get_bi_name`')


#############################
# Concrete Tagger Start
#############################

#FIXME: no notification for updating QOS of volume from cinder.

#FIXME: Add notification about attaching port
#FIXME: Add notification about detaching port

#FIXME: Add notification about network ACL

#FIXME: Adding get_vnc_console notification
#FIXME: create multiple instance from image should based on
#`scheduler.run_instance.start/end` but the end of the notification is not
# the real time that all instance created.

#FIXME: create multiple instance from snapshot should based on
#....(the same reason with the before one)

#####################
# instance snapshot
####################

class InstanceSnapshotStart(_CommonStartTagger):
    event_type = 'compute.instance.snapshot.start'

    def _get_bi_name(self, _message):
        return 'compute.instance.snapshot'


class InstanceSnapshotEnd(_CommonEndTagger):

    event_type = 'compute.instance.snapshot.end'


#####################################
# instance create
#
# The flow of event_type shown below:
#
#     compute.instance.update
#     scheduler.run_instance.start     (only once)
#     scheduler.run_instance.scheduled (the number of instance)
#     scheduler.run_instance.end       (only once)
#     compute.instance.update
#     compute.instance.create.start    (the number of instance)
#     compute.instance.update          (the number of instance)
#     compute.instance.update          (the number of instance)
#     compute.instance.update          (the number of instance)
#     compute.instance.update          (the number of instance)
#     compute.instance.update          (the number of instance)
#     compute.instance.update          (the number of instance)
#     compute.instance.update          (the number of instance)
#     compute.instance.create.end      (the number of instance)
#
####################################

class InstanceCreateStart(_CommonStartTagger):

    event_type = 'compute.instance.create.start'

    def _get_bi_name(self, message):
        try:
            image_type = message['payload']['image_meta']['image_type']
        except (KeyError, TypeError, ValueError):
            image_type = None

        if image_type == 'snapshot':
            bi_name = 'compute.instance.create.from.snapshot'
        else:
            bi_name = 'compute.instance.create.from.image'

        return bi_name


class InstanceCreateEnd(_CommonEndTagger):
    #NOTE(gtt): Creating multiple instances emit multiple 'end' notification.
    #here we only see the first one, then mark the action end.
    event_type = 'compute.instance.create.end'


#######################
# instance delete
######################

class InstanceDeleteStart(_CommonStartTagger):
    event_type = 'compute.instance.delete.start'

    def _get_bi_name(self, _message):
        return 'compute.instance.delete'


class InstanceDeleteEnd(_CommonEndTagger):
    event_type = 'compute.instance.delete.end'


###################################
## instance resize & migrate
#
#   The flow of event_type shown blow:
#
#     compute.instance.update
#     compute.instance.exists
#     compute.instance.resize.prep.start
#     compute.instance.update
#     compute.instance.resize.prep.end *** new_instance_type bob up here
#     compute.instance.update
#     compute.instance.resize.start
#     compute.instance.update
#     compute.instance.resize.end
#     compute.instance.update
#     compute.instance.finish_resize.start
#     compute.instance.update
#     compute.instance.finish_resize.end
#
##################################

class InstanceResizeStart(Tagger):
    event_type = 'compute.instance.resize.prep.start'

    def tag(self, action, message):
        self.fill_request_id_start_at_tenant_name_and_id(action, message)


class InstanceResizePrep(Tagger):

    event_type = 'compute.instance.resize.prep.end'

    def tag(self, action, message):
        old_flavor_id = message['payload']['instance_type_id']
        new_flavor_id = message['payload']['new_instance_type_id']

        if old_flavor_id != new_flavor_id:
            bi_name = 'compute.instance.resize'
        else:
            bi_name = 'compute.instance.migrate'
        self.fill_bi_name(action, bi_name)


class InstanceResizeEnd(_CommonEndTagger):
    event_type = 'compute.instance.finish_resize.end'


######################
# volume create
######################

class VolumeCreateStart(_CommonStartTagger):
    event_type = 'volume.create.start'

    def _get_bi_name(self, _message):
        bi_name = 'volume.create'
        return bi_name


class VolumeCreateEnd(_CommonEndTagger):
    event_type = 'volume.create.end'


######################
# volume delete
######################

class VolumeDeleteStart(_CommonStartTagger):
    event_type = 'volume.delete.start'

    def _get_bi_name(self, _message):
        return 'volume.delete'


class VolumeDeleteEnd(_CommonEndTagger):
    event_type = 'volume.delete.end'


#########################
# volume resize
#########################

class VolumeResizeStart(_CommonStartTagger):
    event_type = 'volume.resize.start'

    def _get_bi_name(self, _message):
        return 'volume.resize'


class VolumeResizeEnd(_CommonEndTagger):
    event_type = 'volume.resize.end'


##########################
# instance attach volume
##########################

class InstanceVolumeAttach(_SyncTagger):
    event_type = 'compute.instance.volume.attach'

    def _get_bi_name(self, _message):
        return 'compute.instance.volume.attach'


##########################
# instance detach volume
##########################

class InstanceVolumeDetach(_SyncTagger):
    event_type = 'compute.instance.volume.detach'

    def _get_bi_name(self, _message):
        return 'compute.instance.volume.detach'


###########################
# network create
###########################

class NetworkCreateStart(_CommonStartTagger):
    event_type = 'network.create.start'

    def _get_bi_name(self, _message):
        return 'network.create'


class NetworkCreateEnd(_CommonEndTagger):
    event_type = 'network.create.end'


###########################
# port create
###########################

class PortCreateStart(_CommonStartTagger):
    event_type = 'port.create.start'

    def _get_bi_name(self, message):
        return 'port.create'


class PortCreateEnd(_CommonEndTagger):
    event_type = 'port.create.end'


#######################################
# Case end
#######################################


def get_taggers():
    """Return all concrete Taggers' object."""
    result = []
    for key, value in globals().iteritems():
        if (inspect.isclass(value) and
                issubclass(value, Tagger) and
                value is not Tagger and
                not key.startswith('_')):
            result.append(value())
    return result
