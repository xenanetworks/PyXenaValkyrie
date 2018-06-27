"""
Base classes and utilities for all Xena Manager (Xena) objects.

:author: yoram@ignissoft.com
"""

import logging

from xenamanager.api.XenaSocket import XenaSocket
from xenamanager.api.KeepAliveThread import KeepAliveThread

logger = logging.getLogger(__name__)


class XenaCliWrapper(object):

    def __init__(self, logger):
        """ Init Xena REST API.

        :param looger: application logger.
        """

        self.logger = logger
        self.chassis_list = {}

    def connect(self, owner):
        self.owner = owner

    def disconnect(self):
        for chassis in self.chassis_list.values():
            chassis.disconnect()
        self.chassis_list = {}

    def add_chassis(self, chassis):
        """
        :param ip: chassis object
        """

        self.chassis_list[chassis] = XenaSocket(self.logger, chassis.ip, chassis.port)
        self.chassis_list[chassis].connect()
        KeepAliveThread(self.chassis_list[chassis]).start()
        self.send_command(chassis, 'c_logon', '"{}"'.format(chassis.password))
        self.send_command(chassis, 'c_owner', '"{}"'.format(chassis.owner))

    def create(self, obj):
        self.send_command(obj, obj.create_command)

    def send_command(self, obj, command, *arguments):
        """ Send command and do not parse output (except for communication errors).

        :param obj: requested object.
        :param command: command to send.
        :param arguments: list of command arguments.
        """
        index_command = obj._build_index_command(command, *arguments)
        self.chassis_list[obj.chassis].sendQueryVerify(index_command)

    def send_command_return(self, obj, command, *arguments):
        """ Send command and wait for single line output. """
        index_command = obj._build_index_command(command, *arguments)
        return obj._extract_return(command, self.chassis_list[obj.chassis].sendQuery(index_command))

    def send_command_return_multilines(self, obj, command, *arguments):
        """ Send command and wait for multiple lines output. """
        index_command = obj._build_index_command(command, *arguments)
        return self.chassis_list[obj.chassis].sendQuery(index_command, True)

    def get_attribute(self, obj, attribute):
        """ Returns single object attribute.

        :param obj: requested object.
        :param attribute: requested attribute to query.
        :returns: returned value.
        :rtype: str
        """
        return self.send_command_return(obj, attribute, '?')

    def get_attributes(self, obj):
        """ Get all object's attributes.

        Sends multi-parameter info/config queries and returns the result as dictionary.

        :param obj: requested object.
        :returns: dictionary of <name, value> of all attributes returned by the query.
        :rtype: dict of (str, str)
        """

        attributes = {}
        for info_config_command in obj.info_config_commands:
            index_commands_values = self.send_command_return_multilines(obj, info_config_command, '?')
            # poor implementation...
            li = obj._get_index_len()
            ci = obj._get_command_len()
            for index_command_value in index_commands_values:
                command = index_command_value.split()[ci].lower()
                if len(index_command_value.split()) > li + 1:
                    value = ' '.join(index_command_value.split()[li+1:]).replace('"', '')
                else:
                    value = None
                attributes[command] = value
        return attributes

    def set_attributes(self, obj, **attributes):
        """ Set attributes.

        :param obj: requested object.
        :param attributes: dictionary of {attribute: value} to set
        """
        for attribute, value in attributes.items():
            self.send_command(obj, attribute, value)
