#
# Created on 2013-3-14
#
# @author: hzyangtk@corp.netease.com
#


class FakeInstance(object):
    """
    Fake VM Instance class
    """
    def __init__(self, uuid='00000000-0000-0000-0000-000000000001',
                 metadata={}, addresses={},
                 tenant_id='0000000000000000000000000000001',
                 name='fake_instance_name',
                 flavor={'id': 'fake_flavor_id'}):
        self.uuid = uuid
        self.metadata = metadata
        self.addresses = addresses
        self.tenant_id = tenant_id
        self.name = name
        self.flavor = flavor
