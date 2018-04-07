"""
Classes and utilities that represents Xena XenaManager-2G port.

:author: yoram@ignissoft.com
"""

import os
import re
from collections import OrderedDict
from enum import Enum

from trafficgenerator.tgn_utils import TgnError

from xenamanager.api.XenaSocket import XenaCommandException
from xenamanager.xena_object import XenaObject
from xenamanager.xena_stream import XenaStream, XenaStreamState


class XenaCaptureBufferType(Enum):
    raw = 0
    text = 1
    pcap = 2


class XenaPort(XenaObject):
    """ Represents Xena port. """

    stats_captions = {'pr_pfcstats': ['total', 'CoS 0', 'CoS 1', 'CoS 2', 'CoS 3', 'CoS 4', 'CoS 5', 'CoS 6', 'CoS 7'],
                      'pr_total': ['bps', 'pps', 'bytes', 'packets'],
                      'pr_notpld': ['bps', 'pps', 'bytes', 'packets'],
                      'pr_extra': ['fcserrors', 'pauseframes', 'arprequests', 'arpreplies', 'pingrequests',
                                   'pingreplies', 'gapcount', 'gapduration'],
                      'pt_total': ['bps', 'pps', 'bytes', 'packets'],
                      'pt_extra': ['arprequests', 'arpreplies', 'pingrequests', 'pingreplies', 'injectedfcs',
                                   'injectedseq', 'injectedmis', 'injectedint', 'injectedtid', 'training'],
                      'pt_notpld': ['bps', 'pps', 'bytes', 'packets']}

    def __init__(self, parent, index):
        """
        :param parent: parent module or session object.
        :param index: port index in format module/port (both 0 based)
        """

        super(self.__class__, self).__init__(objType='port', index=index, parent=parent)
        self._data['name'] = '{}/{}'.format(parent.name, index)
        self.p_info = None

    def inventory(self):
        self.p_info = self.get_attributes('p_info')

    def reserve(self, force):
        """ Reserve port.

        XenaManager-2G -> Reserve/Relinquish Port.

        :param force: True - take forcefully, False - fail if port is reserved by other user
        """

        p_reservation = self.get_attribute('p_reservation')
        if p_reservation == 'RESERVED_BY_YOU':
            return
        elif p_reservation == 'RESERVED_BY_OTHER' and not force:
            raise TgnError('Port {} reserved by {}'.format(self, self.get_attribute('p_reservedby')))
        self.relinquish()
        self.send_command('p_reservation reserve')

    def relinquish(self):
        if self.get_attribute('p_reservation') != 'RELEASED':
            self.send_command('p_reservation relinquish')

    def release(self):
        if self.get_attribute('p_reservation') == 'RESERVED_BY_YOU':
            self.send_command('p_reservation release')

    def reset(self):
        return self.send_command('p_reset')

    def wait_for_up(self, timeout=40):
        self.wait_for_states('P_RECEIVESYNC', timeout, 'IN_SYNC')

    #
    # Configurations.
    #

    def load_config(self, config_file_name):
        """ Load configuration file from xpc file.

        :param config_file_name: full path to the configuration file.
        """

        with open(config_file_name) as f:
            commands = f.read().splitlines()

        for command in commands:
            if not command.startswith(';'):
                try:
                    self.send_command(command)
                except XenaCommandException as e:
                    self.logger.warning(str(e))

        tpld_ids = []
        for index in self.get_attribute('ps_indices').split():
            stream = XenaStream(parent=self, index='{}/{}'.format(self.ref, index))
            tpld_ids.append(stream.get_attribute('ps_tpldid'))
        XenaStream.next_tpld_id = max([XenaStream.next_tpld_id] + [int(t) for t in tpld_ids]) + 1

    def save_config(self, config_file_name):
        """ Save configuration file to xpc file.

        :param config_file_name: full path to the configuration file.
        """

        with open(config_file_name, 'w+') as f:
            f.write('P_RESET\n')
            for line in self.send_command_return_multilines('p_fullconfig ?'):
                f.write(line.split(' ', 1)[1].lstrip())

    def add_stream(self, name=None, tpld_id=None, state=XenaStreamState.enabled):
        """ Add stream.

        :param name: stream description.
        :param tpld_id: TPLD ID. If None the a unique value will be set.
        :param state: new stream state.
        :type state: xenamanager.xena_stream.XenaStreamState
        :return: newly created stream.
        :rtype: xenamanager.xena_stream.XenaStream
        """

        stream = XenaStream(parent=self, index='{}/{}'.format(self.ref, len(self.streams)), name=name)
        stream.send_command('ps_create')
        tpld_id = tpld_id if tpld_id else XenaStream.next_tpld_id
        stream.set_attributes(ps_comment='"{}"'.format(stream.name), ps_tpldid=tpld_id)
        XenaStream.next_tpld_id = max(XenaStream.next_tpld_id + 1, tpld_id + 1)
        stream.set_state(state)
        return stream

    def remove_stream(self, index):
        """ Remove stream.

        :param index: index of stream to remove.
        """

        self.streams[index].del_object_from_parent()

    #
    # Operations.
    #

    def start_traffic(self, blocking=False):
        """ Start port traffic.

        Port -> Start Traffic

        :param blocking: True - start traffic and wait until traffic ends, False - start traffic and return.
        """
        self.session.start_traffic(blocking, self)

    def stop_traffic(self):
        """ Stop port traffic.

        Port -> Stop Traffic
        """
        self.session.stop_traffic(self)

    def start_capture(self):
        """ Start capture on port.

        Capture -> Start Capture
        """
        self.send_command('p_capture', 'on')

    def stop_capture(self):
        """ Stop capture on port.

        Capture -> Stop Capture
        """
        self.send_command('p_capture', 'off')

    #
    # Statistics.
    #

    def clear_stats(self):
        """ Clear att TX and RX statistics counter.

        Port Statistics -> Clear TX Counters, Clear RX Counters
        """
        self.send_command('pt_clear')
        self.send_command('pr_clear')

    def read_port_stats(self):
        """
        :return: dictionary {group name {stat name: value}}.
            Sea XenaPort.stats_captions.
        """

        stats_with_captions = OrderedDict()
        for stat_name in self.stats_captions.keys():
            stats_with_captions[stat_name] = self.read_stat(self.stats_captions[stat_name], stat_name)
        return stats_with_captions

    def read_stream_stats(self):
        """
        :return: dictionary {stream index {stat name: value}}.
            Sea XenaStream.stats_captions.
        """
        stream_stats = OrderedDict()
        for stream in self.streams.values():
            stream_stats[stream] = stream.read_stats()
        return stream_stats

    def read_tpld_stats(self):
        """
        :return: dictionary {tpld index {group name {stat name: value}}}.
            Sea XenaTpld.stats_captions.
        """
        payloads_stats = OrderedDict()
        for tpld in self.tplds.values():
            payloads_stats[tpld] = tpld.read_stats()
        return payloads_stats

    #
    # Properties.
    #

    @property
    def streams(self):
        """
        :return: dictionary {index: object} of all streams.
        """

        return {int(s.ref.split('/')[-1]): s for s in self.get_objects_by_type('stream')}

    @property
    def tplds(self):
        """
        :return: dictionary {index: object} of all current tplds.
        """

        # TPLD has the same index as stream. Since we don't want to override the streams and as TPLDs are temporary and
        # dynamic we create them under port parent (chassis) and erase them before we read them again.
        self.parent.del_objects_by_type('tpld')
        for tpld in self.get_attribute('pr_tplds').split():
            XenaTpld(parent=self.parent, index='{}/{}'.format(self.ref, tpld)).read_stats()
        return {int(s.ref.split('/')[-1]): s for s in self.parent.get_objects_by_type('tpld')}

    @property
    def capture(self):
        """
        :return: capture object.
        :rtype: XenaCapture
        """

        if not self.get_object_by_type('capture'):
            XenaCapture(parent=self)
        return self.get_object_by_type('capture')


class XenaTpld(XenaObject):

    stats_captions = {'pr_tpldtraffic': ['bps', 'pps', 'byt', 'pac'],
                      'pr_tplderrors': ['dummy', 'seq', 'mis', 'pld'],
                      'pr_tpldlatency': ['min', 'avg', 'max', 'avg1sec', 'min1sec', 'max1sec'],
                      'pr_tpldjitter': ['min', 'avg', 'max', 'avg1sec', 'min1sec', 'max1sec']}

    def __init__(self, parent, index):
        """
        :param parent: parent port object.
        :param index: TPLD index in format module/port/tpld.
        """
        super(self.__class__, self).__init__(objType='tpld', index=index, parent=parent)

    def _build_index_command(self, command, *arguments):
        module, port, sid = self.ref.split('/')
        return ('{}/{} {} [{}]' + len(arguments) * ' {}').format(module, port, command, sid, *arguments)

    def _extract_return(self, command, index_command_value):
        module, port, sid = self.ref.split('/')
        return re.sub('{}/{}\s*{}\s*\[{}\]\s*'.format(module, port, command.upper(), sid), '', index_command_value)

    def _get_index_len(self):
        return 2

    def _get_command_len(self):
        return 1

    def read_stats(self):
        """
        :return: dictionary {group name {stat name: value}}.
            Sea XenaTpld.stats_captions.
        """

        stats_with_captions = OrderedDict()
        for stat_name in self.stats_captions.keys():
            stats_with_captions[stat_name] = self.read_stat(self.stats_captions[stat_name], stat_name)
        return stats_with_captions


class XenaCapture(XenaObject):
    """ Represents capture parameters, correspond to the Capture panel of the XenaManager, and deal with configuration
        of the capture criteria and inspection of the captured data from a port.
    """

    def __init__(self, parent):
        super(self.__class__, self).__init__(objType='capture', index=parent.ref, parent=parent)

    def get_packets(self, from_index=0, to_index=None, cap_type=XenaCaptureBufferType.text,
                    file_name=None, tshark=None):
        """ Get captured packets from chassis.

        :param from_index: index of first packet to read.
        :param to_index: index of last packet to read. If None - read all packets.
        :param cap_type: returned capture format. If pcap then file name and tshark must be provided.
        :param file_name: if specified, capture will be saved in file.
        :param tshark: tshark object for pcap type only.
        :type: xenamanager.xena_tshark.Tshark
        :return: list of requested packets, None for pcap type.
        """

        to_index = to_index if to_index else int(self.get_attribute('pc_stats').split()[1])

        raw_packets = []
        for index in range(from_index, to_index):
            raw_packets.append(self.get_attribute('pc_packet [{}]'.format(index)).split('0x')[1])

        if cap_type == XenaCaptureBufferType.raw:
            self._save_captue(file_name, raw_packets)
            return raw_packets

        text_packets = []
        for raw_packet in raw_packets:
            text_packet = ''
            for c, b in zip(range(len(raw_packet)), raw_packet):
                if c % 32 == 0:
                    text_packet += '\n{:06x} '.format(int(c / 2))
                elif c % 2 == 0:
                    text_packet += ' '
                text_packet += b
            text_packets.append(text_packet)

        if cap_type == XenaCaptureBufferType.text:
            self._save_captue(file_name, text_packets)
            return text_packets

        temp_file_name = file_name + '_'
        self._save_captue(temp_file_name, text_packets)
        tshark.text_to_pcap(temp_file_name, file_name)
        os.remove(temp_file_name)

    def _save_captue(self, file_name, packets):
        if file_name:
            with open(file_name, 'w+') as f:
                for packet in packets:
                    f.write(packet)
