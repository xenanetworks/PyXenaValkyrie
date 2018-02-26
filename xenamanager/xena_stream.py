"""
Classes and utilities that represents Xena XenaManager-2G stream.

:author: yoram@ignissoft.com
"""

import re
import binascii
from enum import Enum
from collections import OrderedDict

from pypacker.layer12 import ethernet

from xenamanager.xena_object import XenaObject


class ModifierType(Enum):
    standard = 0
    extended = 1


class ModifierAction(Enum):
    increment = 'INC'
    decrement = 'DEC'
    random = 'RANDOM'


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

    def add_modifier(self, m_type=ModifierType.standard):
        """ Add modifier.

        :param m_type: modifier type - standard or extended.
        :type: xenamanager.xena_stram.ModifierType
        :return: newly created modifier.
        :rtype: xenamanager.xena_stream.XenaModifier
        """

        modifier = XenaModifier(self, index='{}/{}'.format(self.ref, len(self.modifiers)), m_type=m_type)
        if m_type == ModifierType.standard:
            self.set_attribute('ps_modifiercount', len(self.modifiers))
        else:
            self.set_attribute('ps_modifierextcount', len(self.modifiers))
        return modifier

    @property
    def modifiers(self):
        """
        :return: dictionary {index: object} of all modifiers.
        """

        if not self.get_objects_by_type('modifier'):
            ps_modifiercount = int(self.get_attribute('ps_modifiercount'))
            for index in range(ps_modifiercount):
                XenaModifier(self, index='{}/{}'.format(self.ref, index), m_type=ModifierType.standard)
            try:
                ps_modifierextcount = int(self.get_attribute('ps_modifierextcount'))
                for index in range(ps_modifiercount, ps_modifiercount + ps_modifierextcount):
                    XenaModifier(self, index='{}/{}'.format(self.ref, index), m_type=ModifierType.extended)
            except Exception as _:
                pass
        return {int(m.ref.split('/')[-1]): m for m in self.get_objects_by_type('modifier')}


class XenaModifier(XenaObject):

    def __init__(self, parent, index, m_type):
        """
        :param parent: parent stream object.
        :param index: stream index in format module/port/stream.
        :param m_type: modifier type - standard or extended.
        :type: xenamanager.xena_stram.ModifierType
        """

        super(self.__class__, self).__init__(objType='modifier', index=index, parent=parent)
        self.m_type = m_type

    def build_index_command(self, command, *arguments):
        module, port, sid, mid = self.ref.split('/')
        return ('{}/{} {} [{},{}]' + len(arguments) * ' {}').format(module, port, command, sid, mid, *arguments)

    def extract_return(self, command, index_command_value):
        module, port, sid, mid = self.ref.split('/')
        return re.sub('{}/{}\s*{}\s*\[{},{}\]\s*'.
                      format(module, port, command.upper(), sid, mid), '', index_command_value)

    def get_index_len(self):
        return 2

    def get_command_len(self):
        return 1

    def set(self, position, action=ModifierAction.increment, min_val=1, step=1, max_val=65535, repeat=1, mask=0xFFFF,):
        if self.m_type == ModifierType.standard:
            self.set_attribute('ps_modifier', '{} {}0000 {} {}'.format(position, hex(mask), action.value, repeat))
        else:
            self.set_attribute('ps_modifierext', '{} {}0000 {} {}'.format(position, hex(mask), action.value, repeat))
        if action != ModifierAction.random:
            if self.m_type == ModifierType.standard:
                self.set_attribute('ps_modifierrange', '{} {} {}'.format(min_val, step, max_val))
            else:
                self.set_attribute('ps_modifierextrange', '{} {} {}'.format(min_val, step, max_val))

    def get(self):
        attributes = OrderedDict()
        if self.m_type == ModifierType.standard:
            position, mask, action, repeat = self.get_attribute('ps_modifier').split()
        else:
            position, mask, action, repeat = self.get_attribute('ps_modifierext').split()
        attributes['position'] = int(position)
        attributes['mask'] = hex(int(mask[:6], 16))
        attributes['action'] = ModifierAction(action)
        attributes['repeat'] = int(repeat)
        if attributes['action'] != ModifierAction.random:
            if self.m_type == ModifierType.standard:
                min_val, step, max_val = self.get_attribute('ps_modifierrange').split()
            else:
                min_val, step, max_val = self.get_attribute('ps_modifierextrange').split()
            attributes['min_val'] = int(min_val)
            attributes['step'] = int(step)
            attributes['max_val'] = int(max_val)
        return attributes
