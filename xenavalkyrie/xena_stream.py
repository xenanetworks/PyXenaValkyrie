"""
Classes and utilities that represents Xena XenaManager-2G stream.

:author: yoram@ignissoft.com
"""
from __future__ import annotations
import binascii
import re
from collections import OrderedDict
from enum import Enum
from typing import Dict, Optional

from pypacker.layer12.ethernet import Ethernet

import xenavalkyrie.xena_port
from xenavalkyrie.xena_object import XenaObject, XenaObject21
from xenavalkyrie.api.xena_cli import XenaCliWrapper


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
    _info_config_commands = ['ps_config']
    stats_captions = ['bps', 'pps', 'bytes', 'packets']

    next_tpld_id = 0

    def __init__(self, parent: xenavalkyrie.xena_port.XenaPort, index: str, name: Optional[str]='') -> None:
        """
        :param parent: parent port object.
        :param index: stream index in format module/port/stream.
        :param name: stream description.
        """
        super().__init__(parent=parent, objType='stream', index=index, name=name)

    def del_object_from_parent(self):
        self.send_command('ps_delete')
        super(self.__class__, self).del_object_from_parent()

    def set_state(self, state):
        """ Set stream state.

        :param state: new stream state.
        :type state: xenavalkyrie.xena_stream.XenaStreamState
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

    def set_packet_headers(self, headers, l4_checksum=False, raw_header=False):
        """ Set packet header.

        The method will try to set ps_headerprotocol to inform the Xena GUI and tester how to interpret the packet
        header byte sequence specified with PS_PACKETHEADER.
        This is mainly for information purposes, and the stream will transmit the packet header bytes even if no
        protocol segments are specified.
        If the method fails to set some segment it will log a warning and skip setup.

        :param headers: current packet headers. Set this parameter to None if you want to add extended payload at offset 0
        :type headers: pypacker.layer12.ethernet.Ethernet
        :param l4_checksum: True - set tcp/udp checksum flag, False - do not set
        """

        if headers:
            body_handler = headers
            ps_headerprotocol = []
            while body_handler:
                segment = pypacker_2_xena.get(str(body_handler).split('\n')[0].split('.')[-1].lower(), None)
                if segment == 'flowcontrol' or segment == 'rawheader':
                    # Skip this iteration if:
                    #   - It is a flowcontrol header and check if what follows is Pause or PFC
                    #   - It is a raw header
                    body_handler = body_handler.upper_layer
                    continue

                if not segment:
                    self.logger.warning(f'pypacker header not in conversion list')
                    break
                ps_headerprotocol.append(segment)
                if type(body_handler) is Ethernet and body_handler.vlan:
                    for _ in range(len(body_handler.vlan)):
                        ps_headerprotocol.append('vlan')
                body_handler = body_handler.upper_layer
            if l4_checksum:
                l4 = headers.upper_layer.upper_layer
                l4.sum_au_active = False
                l4.sum = 0
                if 'udp' in ps_headerprotocol:
                    ps_headerprotocol[ps_headerprotocol.index('udp')] = 'udpcheck'
                if 'tcp' in ps_headerprotocol:
                    ps_headerprotocol[ps_headerprotocol.index('tcp')] = 'tcpcheck'
            
            self.set_attributes(ps_headerprotocol=' '.join(ps_headerprotocol))

            headers_str = binascii.hexlify(headers.bin())
            bin_headers = '0x' + headers_str.decode('utf-8')

            if raw_header:
                self.set_attributes(ps_headerprotocol = -1*int((len(bin_headers)-2)/2))

            self.set_attributes(ps_packetheader=bin_headers)

        else:

            if raw_header:
                self.set_attributes(ps_headerprotocol = "")


    def set_extended_payload(self, extended_payload):
        """ Set the extended payload for the stream.

        :param extended_payload: A hexadecimal string representing the extended payload.

        """
        self.set_attributes(ps_extpayload = '0x' + extended_payload.decode('utf-8'))

    #
    # Modifiers.
    #

    def add_modifier(self, m_type=XenaModifierType.standard, **kwargs):
        """ Add modifier.

        :param m_type: modifier type - standard or extended.
        :type: xenavalkyrie.xena_stram.ModifierType
        :return: newly created modifier.
        :rtype: xenavalkyrie.xena_stream.XenaModifier
        """

        if m_type == XenaModifierType.standard:
            modifier = XenaModifier(self, index='{}/{}'.format(self.index, len(self.modifiers)))
        else:
            modifier = XenaXModifier(self, index='{}/{}'.format(self.index, len(self.xmodifiers)))
        modifier._create()
        modifier.get()
        modifier.set(**kwargs)
        return modifier

    def remove_modifier(self, index, m_type=XenaModifierType.standard):
        """ Remove modifier.

        :param m_type: modifier type - standard or extended.
        :param index: index of modifier to remove.
        """

        if m_type == XenaModifierType.standard:
            current_modifiers = OrderedDict(self.modifiers)
            del current_modifiers[index]

            self.set_attributes(ps_modifiercount=0)
            self.del_objects_by_type('modifier')

        else:
            current_modifiers = OrderedDict(self.xmodifiers)
            del current_modifiers[index]

            self.set_attributes(ps_modifierextcount=0)
            self.del_objects_by_type('xmodifier')

        for modifier in current_modifiers.values():
            self.add_modifier(m_type,
                              mask=modifier.mask, action=modifier.action, repeat=modifier.repeat,
                              min_val=modifier.min_val, step=modifier.step, max_val=modifier.max_val)

    #
    # Properties.
    #

    @property
    def modifiers(self) -> Dict[int, XenaModifier]:
        """
        :return: dictionary {index: object} of standard modifiers.
        """
        if not self.get_objects_by_type('modifier'):
            for index in range(int(self.get_attribute('ps_modifiercount'))):
                XenaModifier(self, index='{}/{}'.format(self.index, index)).get()
        return {s.id: s for s in self.get_objects_by_type('modifier')}

    @property
    def xmodifiers(self):
        """
        :return: dictionary {index: object} of extended modifiers.
        """
        if not self.get_objects_by_type('xmodifier'):
            try:
                for index in range(int(self.get_attribute('ps_modifierextcount'))):
                    XenaXModifier(self, index='{}/{}'.format(self.index, index)).get()
            except Exception as _:
                pass
        return {s.id: s for s in self.get_objects_by_type('xmodifier')}


class _XenaModifierBase(XenaObject):

    def __init__(self, objType, parent, index):
        super(_XenaModifierBase, self).__init__(objType=objType, index=index, parent=parent)

    def _create(self):
        if type(self.api) is XenaCliWrapper:
            if type(self) == XenaModifier:
                self.parent.set_attributes(ps_modifiercount=len(self.parent.modifiers))
            else:
                self.parent.set_attributes(ps_modifierextcount=len(self.parent.xmodifiers))
        else:
            super(_XenaModifierBase, self)._create()

    def set(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if type(self) == XenaModifier:
            self.set_attributes(ps_modifier='{} {} {} {}'.format(self.position, self.mask,
                                                                 self.action.value, self.repeat))
        else:
            self.set_attributes(ps_modifierext='{} {} {} {}'.format(self.position, self.mask,
                                                                    self.action.value, self.repeat))
        if self.action != XenaModifierAction.random:
            if type(self) == XenaModifier:
                self.set_attributes(ps_modifierrange='{} {} {}'.format(self.min_val, self.step, self.max_val))
            else:
                self.set_attributes(ps_modifierextrange='{} {} {}'.format(self.min_val, self.step, self.max_val))

    def get(self):
        if type(self) == XenaModifier:
            position, mask, action, repeat = self.get_attribute('ps_modifier').split()
        else:
            position, mask, action, repeat = self.get_attribute('ps_modifierext').split()
        self.position = int(position)
        self.mask = '0x{:x}'.format(int(mask, 16))
        self.action = XenaModifierAction(action)
        self.repeat = int(repeat)
        if self.action != XenaModifierAction.random:
            if type(self) == XenaModifier:
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
        module, port, sid, mid = self.index.split('/')
        return ('{}/{} {} [{},{}]' + len(arguments) * ' {}').format(module, port, command, sid, mid, *arguments)

    def _extract_return(self, command, index_command_value):
        module, port, sid, mid = self.index.split('/')
        return re.sub(r'{}/{}\s*{}\s*\[{},{}\]\s*'.format(module, port, command.upper(), sid, mid),
                      '', index_command_value)

    def _get_index_len(self):
        return 2

    def _get_command_len(self):
        return 1


class XenaModifier(_XenaModifierBase):

    _info_config_commands = ['ps_modifier', 'ps_modifierrange']

    def __init__(self, parent, index):
        """
        :param parent: parent stream object.
        :param index: modifier index in format module/port/stream/modifier.
        """
        super(self.__class__, self).__init__(objType='modifier', index=index, parent=parent)


class XenaXModifier(_XenaModifierBase):

    _info_config_commands = ['ps_modifierext', 'ps_modifierextrange']

    def __init__(self, parent, index):
        """
        :param parent: parent stream object.
        :param index: modifier index in format module/port/stream/modifier.
        """
        super(self.__class__, self).__init__(objType='xmodifier', index=index, parent=parent)


pypacker_2_xena = {'ethernet'      : 'ethernet',
                   'dot1q'         : 'vlan',
                   'arp'           : 'arp',
                   'ip'            : 'ip',
                   'ip6'           : 'ipv6',
                   'udp'           : 'udp',
                   'tcp'           : 'tcp',
                   'icmp'          : 'icmp',
                   'dhcp'          : '39',
                   'flowcontrol'   : 'flowcontrol',
                   'pause'         : 'macctrl',
                   'pfc'           : 'macctrlpfc',
                   'rawheader'     : 'rawheader'
                   }
