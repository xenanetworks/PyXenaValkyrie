"""
Classes and utilities that represents Xena XenaManager-2G FILTER TERMS and FILTER DEFINITION panels.

:author: yoram@ignissoft.com
"""

from enum import Enum

from xenavalkyrie.xena_object import XenaObject21


class XenaFilterState(Enum):
    on = 'ON'
    off = 'OFF'


class XenaFilter(XenaObject21):

    create_command = 'pf_create'
    _info_config_commands = ['pf_config', 'pf_condition']

    def __init__(self, parent, index, name=''):
        """
        :param parent: parent port object.
        :param index: filter index in format module/port/filter.
        :param name: filter comment.
        """

        super(self.__class__, self).__init__(objType='filter', index=index, parent=parent, name=name)

    def del_object_from_parent(self):
        self.set_state(XenaFilterState.off)
        self.send_command('pf_delete')
        super(self.__class__, self).del_object_from_parent()

    def set_state(self, state):
        """ Set filter state.

        :param state: new filter state.
        :type stae: xenavalkyrie.xena_filter.XenaFilterState
        """
        self.set_attributes(pf_enable=state.value)


class XenaMatch(XenaObject21):

    create_command = 'pm_create'
    _info_config_commands = ['pm_config']

    def __init__(self, parent, index):
        """
        :param parent: parent port object.
        :param index: match index in format module/port/match.
        """

        super(self.__class__, self).__init__(objType='match', index=index, parent=parent)

    def del_object_from_parent(self):
        self.send_command('pm_delete')
        super(self.__class__, self).del_object_from_parent()


class XenaLength(XenaObject21):

    create_command = 'pl_create'
    _info_config_commands = ['pl_length']

    def __init__(self, parent, index):
        """
        :param parent: parent port object.
        :param index: length index in format module/port/length.
        """

        super(self.__class__, self).__init__(objType='length', index=index, parent=parent)

    def del_object_from_parent(self):
        self.send_command('pl_delete')
        super(self.__class__, self).del_object_from_parent()
