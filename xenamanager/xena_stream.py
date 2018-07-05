"""
Classes and utilities that represents Xena XenaManager-2G stream.

:author: yoram@ignissoft.com
"""

import re
import binascii
from enum import Enum
from collections import OrderedDict

from pypacker.layer12.ethernet import Ethernet

from xenamanager.xena_object import XenaObject, XenaObject21


class XenaStreamState(Enum):
    enabled = 'ON'
    disabled = 'OFF'
    suspended = 'SUPPRESS'


class XenaModifierType(Enum):
    standard = 0
    extended = 1


class XenaModifierAction(Enum):
    increment = 'INC'
    decrement = 'DEC'
    random = 'RANDOM'


class XenaStream(XenaObject21):

    create_command = 'ps_create'
    info_config_commands = ['ps_config']
    stats_captions = ['bps', 'pps', 'bytes', 'packets']

    next_tpld_id = 0

    def __init__(self, parent, index, name=''):
        """
        :param parent: parent port object.
        :param index: stream index in format module/port/stream.
        :param name: stream description.
        """

        super(self.__class__, self).__init__(objType='stream', index=index, parent=parent, name=name)

    def del_object_from_parent(self):
        self.send_command('ps_delete')
        super(self.__class__, self).del_object_from_parent()

    def set_state(self, state):
        """ Set stream state.

        :param state: new stream state.
        :type stae: xenamanager.xena_stream.XenaStreamState
        """
        self.set_attributes(ps_enable=state.value)

    def read_stats(self):
        """
        :return: dictionary {stat name: value}
            See XenaStream.stats_captions
        """
        return self.read_stat(XenaStream.stats_captions, 'pt_stream')

    def get_packet_headers(self):
        """
        :return: current packet headers
        :rtype: pypacker.layer12.ethernet.Ethernet
        """

        bin_headers = self.get_attribute('ps_packetheader')
        return Ethernet(binascii.unhexlify(bin_headers[2:]))

    def set_packet_headers(self, headers):
        """ Set packet header.

        The method will try to set ps_headerprotocol to inform the Xena GUI and tester how to interpret the packet
        header byte sequence specified with PS_PACKETHEADER.
        This is mainly for information purposes, and the stream will transmit the packet header bytes even if no
        protocol segments are specified.
        If the method fails to set some segment it will log a warning and skip setup.

        :param headers: current packet headers
        :type headers: pypacker.layer12.ethernet.Ethernet
        """

        bin_headers = '0x' + binascii.hexlify(headers.bin()).decode('utf-8')
        self.set_attributes(ps_packetheader=bin_headers)

        body_handler = headers
        ps_headerprotocol = []
        while body_handler:
            segment = pypacker_2_xena.get(str(body_handler).split('(')[0].lower(), None)
            if not segment:
                self.logger.warning('pypacker header {} not in conversion list'.format(segment))
                return
            ps_headerprotocol.append(segment)
            if type(body_handler) is Ethernet and body_handler.vlan:
                ps_headerprotocol.append('vlan')
            body_handler = body_handler.body_handler
        self.set_attributes(ps_headerprotocol=' '.join(ps_headerprotocol))

    #
    # Modifiers.
    #

    def add_modifier(self, position, m_type=XenaModifierType.standard, **kwargs):
        """ Add modifier.

        :param position: modifier position.
        :param m_type: modifier type - standard or extended.
        :type: xenamanager.xena_stram.ModifierType
        :return: newly created modifier.
        :rtype: xenamanager.xena_stream.XenaModifier
        """

        modifier_index = len(self.modifiers)
        if m_type == XenaModifierType.standard:
            modifier_index = len(self.standard_modifiers)
            self.set_attributes(ps_modifiercount=modifier_index + 1)
        else:
            modifier_index = len(self.extended_modifiers)
            self.set_attributes(ps_modifierextcount=modifier_index + 1)
        modifier = XenaModifier(self, index='{}/{}'.format(self.index, modifier_index), m_type=m_type)
        modifier.position = position
        modifier.set(**kwargs)
        return modifier

    def remove_modifier(self, position):
        """ Remove modifier.

        :param position: position of modifier to remove.
        """

        current_modifiers = OrderedDict(self.modifiers)
        del current_modifiers[position]

        self.set_attributes(ps_modifiercount=0)
        try:
            self.set_attributes(ps_modifierextcount=0)
        except Exception as _:
            pass
        self.del_objects_by_type('modifier')

        for modifier in current_modifiers.values():
            self.add_modifier(modifier.position, modifier.m_type).set(mask=modifier.mask,
                                                                      action=modifier.action,
                                                                      repeat=modifier.repeat,
                                                                      min_val=modifier.min_val,
                                                                      step=modifier.step,
                                                                      max_val=modifier.max_val)

    #
    # Properties.
    #

    @property
    def modifiers(self):
        """
        :return: dictionary {position: object} of all modifiers.
        """

        if not self.get_objects_by_type('modifier'):
            for index in range(int(self.get_attribute('ps_modifiercount'))):
                XenaModifier(self, index='{}/{}'.format(self.index, index), m_type=XenaModifierType.standard)
            try:
                for index in range(int(self.get_attribute('ps_modifierextcount'))):
                    XenaModifier(self, index='{}/{}'.format(self.index, index), m_type=XenaModifierType.extended)
            except Exception as _:
                pass
        return {m.position: m for m in self.get_objects_by_type('modifier')}

    @property
    def standard_modifiers(self):
        """
        :return: dictionary {position: object} of standard modifiers.
        """
        return {p: m for p, m in self.modifiers.items() if m.m_type == XenaModifierType.standard}

    @property
    def extended_modifiers(self):
        """
        :return: dictionary {position: object} of extended modifiers.
        """
        return {p: m for p, m in self.modifiers.items() if m.m_type == XenaModifierType.extended}


class XenaModifier(XenaObject):

    info_config_commands = ['ps_modifier', 'ps_modifierrange']

    def __init__(self, parent, index, m_type):
        """
        :param parent: parent stream object.
        :param index: modifier index in format module/port/stream/modifier.
        :param m_type: modifier type - standard or extended.
        :type: xenamanager.xena_stram.ModifierType
        """

        sid = parent.index.split('/')[-1]
        self.mid = index.split('/')[-1]
        if m_type == XenaModifierType.standard:
            command = 'ps_modifier'
            self.info_config_commands = ['ps_modifier', 'ps_modifierrange']
        else:
            command = 'ps_modifierext'
            self.info_config_commands = ['ps_modifierext', 'ps_modifierextrange']
        reply = parent.parent.send_command_return('{} [{},{}]'.format(command, sid, self.mid), '?')

        index = '/'.join(index.split('/')[:-1]) + '/' + reply.split()[-4]
        super(self.__class__, self).__init__(objType='modifier', index=index, parent=parent)
        self.m_type = m_type
        self.get()

    def set(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if self.m_type == XenaModifierType.standard:
            self.set_attributes(ps_modifier='{} {} {} {}'.format(self.position, self.mask,
                                                                 self.action.value, self.repeat))
        else:
            self.set_attributes(ps_modifierext='{} {} {} {}'.format(self.position, self.mask,
                                                                    self.action.value, self.repeat))
        if self.action != XenaModifierAction.random:
            if self.m_type == XenaModifierType.standard:
                self.set_attributes(ps_modifierrange='{} {} {}'.format(self.min_val, self.step, self.max_val))
            else:
                self.set_attributes(ps_modifierextrange='{} {} {}'.format(self.min_val, self.step, self.max_val))

    def get(self):
        if self.m_type == XenaModifierType.standard:
            position, mask, action, repeat = self.get_attribute('ps_modifier').split()
        else:
            position, mask, action, repeat = self.get_attribute('ps_modifierext').split()
        self.position = int(position)
        self.mask = '0x{:x}'.format(int(mask, 16))
        self.action = XenaModifierAction(action)
        self.repeat = int(repeat)
        if self.action != XenaModifierAction.random:
            if self.m_type == XenaModifierType.standard:
                min_val, step, max_val = self.get_attribute('ps_modifierrange').split()
            else:
                min_val, step, max_val = self.get_attribute('ps_modifierextrange').split()
            self.min_val = int(min_val)
            self.step = int(step)
            self.max_val = int(max_val)

    #
    # Private methods.
    #

    def _build_index_command(self, command, *arguments):
        module, port, sid, _ = self.index.split('/')
        return ('{}/{} {} [{},{}]' + len(arguments) * ' {}').format(module, port, command, sid, self.mid, *arguments)

    def _extract_return(self, command, index_command_value):
        module, port, sid, _ = self.index.split('/')
        return re.sub('{}/{}\s*{}\s*\[{},{}\]\s*'.
                      format(module, port, command.upper(), sid, self.mid), '', index_command_value)

    def _get_index_len(self):
        return 2

    def _get_command_len(self):
        return 1


pypacker_2_xena = {'ethernet': 'ethernet',
                   'arp': 'arp',
                   'ip': 'ip',
                   'ip6': 'ipv6',
                   'udp': 'udp',
                   'tcp': 'tcp',
                   'icmp': 'icmp',
                   }
