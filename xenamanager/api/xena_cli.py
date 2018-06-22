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

    def disconnect(self, chassis):
        self.chassis_list[chassis].disconnect()

    def add_chassis(self, chassis):
        """
        :param ip: chassis object
        """

        self.chassis_list[chassis] = XenaSocket(self.logger, chassis.ip, chassis.port)
        self.chassis_list[chassis].connect()
        KeepAliveThread(self.chassis_list[chassis]).start()

    def send_command(self, obj, command, *arguments):
        """ Send command and do not parse output (except for communication errors). """
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

    def is_connected(self, obj):
        return self.chassis_list[obj.chassis].is_connected()
