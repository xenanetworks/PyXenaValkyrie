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
        if 'name' not in data or data['name'] is None:
            data['name'] = data['objType'] + ' ' + data['objRef'].replace(' ', '/')
        super(XenaObject, self).__init__(**data)
        if self.ref:
            self.id = int(self.ref.split('/')[-1])

    def _build_index_command(self, command, *arguments):
        return ('{} {}' + len(arguments) * ' {}').format(self.ref, command, *arguments)

    def _extract_return(self, command, index_command_value):
        return re.sub('{}\s*{}\s*'.format(self.ref, command.upper()), '', index_command_value)

    def _get_index_len(self):
        return len(self.ref.split())

    def _get_command_len(self):
        return len(self.ref.split())

    def send_command(self, command, *arguments):
        """ Send command and do not parse output (except for communication errors). """
        index_command = self._build_index_command(command, *arguments)
        self.api.sendQueryVerify(index_command)

    def send_command_return(self, command, *arguments):
        """ Send command and wait for single line output. """
        index_command = self._build_index_command(command, *arguments)
        return self._extract_return(command, self.api.sendQuery(index_command))

    def send_command_return_multilines(self, command, *arguments):
        """ Send command and wait for multiple lines output. """
        index_command = self._build_index_command(command, *arguments)
        return self.api.sendQuery(index_command, True)

    def set_attributes(self, **attributes):
        """
        :param attributes: dictionary of {attribute: value} to set
        """
        for attribute, value in attributes.items():
            self.send_command(attribute, value)

    def get_attribute(self, attribute):
        """ Sends single-parameter query and returns the result.

        :param attribute: attribute (e.g. p_config, ps_config) to query.
        :returns: returned value.
        :rtype: str
        """
        return self.send_command_return(attribute, '?')

    def get_attributes(self, attribute):
        """ Sends multi-parameter query and returns the result as dictionary.

        :param attribute: multi-parameter attribute (e.g. p_config, ps_config) to query.
        :returns: dictionary of <attribute, value> of all attributes returned by the query.
        :rtype: dict of (str, str)
        """

        index_commands_values = self.send_command_return_multilines(attribute, '?')
        # poor implementation...
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
