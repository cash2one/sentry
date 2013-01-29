#
# Created on 2012-11-16
#
# @author: hzyangtk
#

from abc import ABCMeta, abstractmethod


class Filter(object):
    '''
    super class of all filters
    '''

    __metaclass__ = ABCMeta

    @abstractmethod
    def init_filter(self):
        pass

    @abstractmethod
    def register_filter(self):
        pass

    @abstractmethod
    def filter(self):
        pass
