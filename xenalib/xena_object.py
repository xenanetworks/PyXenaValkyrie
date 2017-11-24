"""
Base classes and utilities for all Xena Manager (Xena) objects.

:author: yoram@ignissoft.com
"""

import re
import logging

from trafficgenerator.tgn_object import TgnObject

logger = logging.getLogger(__name__)


class XenaObject(TgnObject):

    def __init__(self, **data):
        data['objRef'] = str(data['index'])
        super(XenaObject, self).__init__(**data)
        self._data['name'] = self.type + ' ' + self.ref.replace(' ', '/')

    def build_index_command(self, command, *arguments):
        return ('{} {}' + len(arguments) * ' {}').format(self.ref, command, *arguments)

    def send_command(self, command, *arguments):
        index_command = self.build_index_command(command, *arguments)
        return self.api.sendQueryVerify(index_command)

    def set_attribute(self, attribute, value):
        return self.send_command(attribute, value)

    def get_attribute(self, attribute):
        index_command = self.build_index_command(attribute, '?')
        index_command_value = self.api.sendQuery(index_command)
        return re.sub('{}\s*{}\s*'.format(self.ref, attribute.upper()), '', index_command_value)

    def get_attributes(self, attribute):
        index_command = self.build_index_command(attribute, '?')
        index_commands_values = self.api.sendQuery(index_command, True)
        li = len(self.ref.split())
        attributes = {}
        for index_command_value in index_commands_values:
            command = index_command_value.split()[li].lower()
            if len(index_command_value.split()) > li + 1:
                value = ' '.join(index_command_value.split()[li+1:]).replace('"', '')
            else:
                value = None
            attributes[command] = value
        return attributes
