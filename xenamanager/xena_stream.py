"""
Classes and utilities that represents Xena XenaManager-2G stream.

:author: yoram@ignissoft.com
"""

import re
import binascii

from pypacker.layer12 import ethernet

from xenamanager.xena_object import XenaObject


class XenaStream(XenaObject):

    stats_captions = ['bps', 'pps', 'bytes', 'packets']

    def __init__(self, parent, index):
        """
        :param parent: parent port object.
        :param index: stream index in format module/port/stream.
        """

        super(self.__class__, self).__init__(objType='stream', index=index, parent=parent)

    def build_index_command(self, command, *arguments):
        module, port, sid = self.ref.split('/')
        return ('{}/{} {} [{}]' + len(arguments) * ' {}').format(module, port, command, sid, *arguments)

    def extract_return(self, command, index_command_value):
        module, port, sid = self.ref.split('/')
        return re.sub('{}/{}\s*{}\s*\[{}\]\s*'.format(module, port, command.upper(), sid), '', index_command_value)

    def get_index_len(self):
        return 2

    def get_command_len(self):
        return 1

    def read_stats(self):
        """
        :return: dictionary {stat name: value}
            Sea XenaStream.stats_captions
        """
        return self.read_stat(self.stats_captions, 'pt_stream')

    def get_packet_headers(self):
        """
        :return: current packet headers
        :rtype: pypacker.layer12.ethernet
        """

        bin_headers = self.get_attribute('ps_packetheader')
        return ethernet.Ethernet(binascii.unhexlify(bin_headers[2:]))

    def set_packet_headers(self, headers):
        """
        :param headers: current packet headers
        :type headers: pypacker.layer12.ethernet
        """

        bin_headers = '0x' + binascii.hexlify(headers.bin()).decode('utf-8')
        self.set_attribute('ps_packetheader', bin_headers)
