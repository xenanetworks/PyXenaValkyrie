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
        if 'objRef' not in data:
            data['objRef'] = str(data['index'])
        if 'name' not in data:
            data['name'] = data['objType'] + ' ' + data['objRef'].replace(' ', '/')
        super(XenaObject, self).__init__(**data)

    def _build_index_command(self, command, *arguments):
        return ('{} {}' + len(arguments) * ' {}').format(self.ref, command, *arguments)

    def _extract_return(self, command, index_command_value):
        return re.sub('{}\s*{}\s*'.format(self.ref, command.upper()), '', index_command_value)

    def _get_index_len(self):
        return len(self.ref.split())

    def _get_command_len(self):
        return len(self.ref.split())

    def send_command(self, command, *arguments):
        index_command = self._build_index_command(command, *arguments)
        self.api.sendQueryVerify(index_command)

    def send_command_return(self, command, *arguments):
        index_command = self._build_index_command(command, *arguments)
        return self._extract_return(command, self.api.sendQuery(index_command))

    def set_attribute(self, attribute, value):
        return self.send_command(attribute, value)

    def get_attribute(self, attribute):
        return self.send_command_return(attribute, '?')

    def get_attributes(self, attribute):
        index_command = self._build_index_command(attribute, '?')
        index_commands_values = self.api.sendQuery(index_command, True)
        # poor implementation
        li = self._get_index_len()
        ci = self._get_command_len()
        attributes = {}
        for index_command_value in index_commands_values:
            command = index_command_value.split()[ci].lower()
            if len(index_command_value.split()) > li + 1:
                value = ' '.join(index_command_value.split()[li+1:]).replace('"', '')
            else:
                value = None
            attributes[command] = value
        return attributes

    def wait_for_states(self, attribute, timeout=40, *states):
        for _ in range(timeout):
            if self.get_attribute(attribute).lower() in [s.lower() for s in states]:
                return
            time.sleep(1)
        raise TgnError('{} failed to reach state {}, state is {} after {} seconds'.
                       format(attribute, states, self.get_attribute(attribute), timeout))

    def read_stat(self, captions, stat_name):
        return dict(zip(captions, [int(v) for v in self.get_attribute(stat_name).split()]))

    #
    # Implement abstract API methods.
    #

    def get_children(self, *types):
        pass

    def get_objects_from_attribute(self, attribute):
        pass
