"""
Base classes and utilities for all Xena Manager (Xena) objects.

:author: yoram@ignissoft.com
"""

import time
import re
import logging
from collections import OrderedDict

from trafficgenerator.tgn_utils import TgnError
from trafficgenerator.tgn_object import TgnObject, TgnObjectsDict

logger = logging.getLogger(__name__)


class XenaAttributeError(TgnError):
    pass


class XenaObjectsDict(TgnObjectsDict):

    def __getitem__(self, key):
        """ Override default implementation and allow access with index as well. """
        if TgnObjectsDict.__getitem__(self, key) is not None:
            return TgnObjectsDict.__getitem__(self, key)
        else:
            for obj in self:
                if obj.index == key:
                    return OrderedDict.__getitem__(self, obj)


class XenaObject(TgnObject):
    """ Base class for all Xena objects. """

    def __init__(self, **data):
        if data['parent']:
            self.session = data['parent'].session
            self.chassis = data['parent'].chassis
        if 'objRef' not in data:
            data['objRef'] = '{}/{}/{}'.format(data['parent'].ref, data['objType'], data['index'].split('/')[-1])
        if 'name' not in data:
            data['name'] = data['index']
        super(XenaObject, self).__init__(**data)

    def obj_index(self):
        """
        :return: object index.
        """
        return str(self._data['index'])
    index = property(obj_index)

    def obj_id(self):
        """
        :return: object ID.
        """
        return int(self.index.split('/')[-1]) if self.index else None
    id = property(obj_id)

    def _create(self):
        self.api.create(self)

    def send_command(self, command, *arguments):
        """ Send command with no output.

        :param command: command to send.
        :param arguments: list of command arguments.
        """
        self.api.send_command(self, command, *arguments)

    def send_command_return(self, command, *arguments):
        """ Send command and wait for single line output. """
        return self.api.send_command_return(self, command, *arguments)

    def send_command_return_multilines(self, command, *arguments):
        """ Send command and wait for multiple lines output. """
        return self.api.send_command_return_multilines(self, command, *arguments)

    def set_attributes(self, **attributes):
        """ Sets list of attributes.

        :param attributes: dictionary of {attribute: value} to set.
        """
        try:
            self.api.set_attributes(self, **attributes)
        except Exception as e:
            if '<notwritable>' in repr(e).lower() or '<badvalue>' in repr(e).lower():
                raise XenaAttributeError(e)
            else:
                raise e

    def get_attribute(self, attribute):
        """ Returns single object attribute.

        :param attribute: requested attribute to query.
        :returns: returned value.
        :rtype: str
        """
        try:
            return self.api.get_attribute(self, attribute)
        except Exception as e:
            if '#syntax error' in repr(e).lower() or 'keyerror' in repr(e).lower():
                raise XenaAttributeError(e)
            else:
                raise e

    def get_attributes(self):
        """ Returns all object's attributes.

        :returns: dictionary of <name, value> of all attributes.
        :rtype: dict of (str, str)
        """
        return self.api.get_attributes(self)

    def wait_for_states(self, attribute, timeout=40, *states):
        for _ in range(timeout):
            if self.get_attribute(attribute).lower() in [s.lower() for s in states]:
                return
            time.sleep(1)
        raise TgnError('{} failed to reach state {}, state is {} after {} seconds'.
                       format(attribute, states, self.get_attribute(attribute), timeout))

    def read_stat(self, captions, stat_name):
        return dict(zip(captions, self.api.get_stats(self, stat_name)))

    #
    # Private methods.
    #

    def _build_index_command(self, command, *arguments):
        return ('{} {}' + len(arguments) * ' {}').format(self.index, command, *arguments)

    def _extract_return(self, command, index_command_value):
        return re.sub('{}\s*{}\s*'.format(self.index, command.upper()), '', index_command_value)

    def _get_index_len(self):
        return len(self.index.split())

    def _get_command_len(self):
        return len(self.index.split())


class XenaObject21(XenaObject):
    """ Base class for all Xena objects with index_len = 2 and command_len = 1. """

    #
    # Private methods.
    #

    def _build_index_command(self, command, *arguments):
        module, port, sid = self.index.split('/')
        return ('{}/{} {} [{}]' + len(arguments) * ' {}').format(module, port, command, sid, *arguments)

    def _extract_return(self, command, index_command_value):
        module, port, sid = self.index.split('/')
        return re.sub('{}/{}\s*{}\s*\[{}\]\s*'.format(module, port, command.upper(), sid), '', index_command_value)

    def _get_index_len(self):
        return 2

    def _get_command_len(self):
        return 1
