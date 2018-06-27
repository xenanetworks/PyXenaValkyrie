"""
Base classes and utilities for all Xena Manager (Xena) objects.

:author: yoram@ignissoft.com
"""

import time
import re
import logging

from trafficgenerator.tgn_utils import TgnError
from trafficgenerator.tgn_object import TgnObject

logger = logging.getLogger(__name__)


class XenaObject(TgnObject):

    def __init__(self, **data):
        if data['parent']:
            self.session = data['parent'].session
            self.chassis = data['parent'].chassis
        if 'objRef' not in data:
            data['objRef'] = '{}/{}/{}'.format(data['parent'].ref, data['objType'], data['index'].split('/')[-1])
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

    def _build_index_command(self, command, *arguments):
        return ('{} {}' + len(arguments) * ' {}').format(self.index, command, *arguments)

    def _extract_return(self, command, index_command_value):
        return re.sub('{}\s*{}\s*'.format(self.index, command.upper()), '', index_command_value)

    def _get_index_len(self):
        return len(self.index.split())

    def _get_command_len(self):
        return len(self.index.split())

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
        """
        :param attributes: dictionary of {attribute: value} to set
        """
        for attribute, value in attributes.items():
            self.send_command(attribute, value)

    def get_attribute(self, attribute):
        """ Returns single object attribute.

        :param attribute: requested attribute to query.
        :returns: returned value.
        :rtype: str
        """
        return self.api.get_attribute(self, attribute)

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
        return dict(zip(captions, [int(v) for v in self.get_attribute(stat_name).split()]))
