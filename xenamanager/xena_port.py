"""
Classes and utilities that represents Xena XenaManager-2G port.

:author: yoram@ignissoft.com
"""

import re
from collections import OrderedDict

from trafficgenerator.tgn_utils import TgnError
from trafficgenerator.tgn_object import TgnObjectsDict

from xenamanager.api.XenaSocket import XenaCommandException
from xenamanager.xena_object import XenaObject
from xenamanager.xena_stream import XenaStream


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
                    self.logger.warning(e.message)

        for index in self.get_attribute('ps_indices').split():
            XenaStream(parent=self, index='{}/{}'.format(self.ref, index))

    def add_stream(self):
        """ Add stream.

        :return: newly created stream.
        :rtype: xenamanager.xena_stream.XenaStream
        """

        return XenaStream(self, index='{}/{}'.format(self.ref, len(self.streams)))

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
        self.session.start_traffic(blocking)

    def stop_traffic(self):
        """ Stop port traffic.

        Port -> Stop Traffic
        """
        self.session.stop_traffic()

    def start_capture(self):
        """ Not implemented yet.

        Capture -> Start Capture
        """
        self.send_command('p_capture', 'on')

    def stop_capture(self):
        """ Not implemented yet.

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
    """ Represents cappture parameters, correspond to the Capture panel of the XenaManager, and deal with configuration
        of the capture criteria and inspection of the captured data from a port.
    """

    def __init__(self, parent):
        super(self.__class__, self).__init__(objType='capture', index=parent.ref, parent=parent)

    def get_packet(self, index):
        return self.get_attribute('pc_packet [{}]'.format(index)).split('0x')[1]

    def get_packets(self, from_index=1, to_index=None):
        to_index = to_index if to_index else int(self.get_attribute('pc_stats').split()[1])
        packets = []
        for index in range(from_index, to_index + 1):
            packet = self.get_packet(index)
            pcap_packet = ''
            for c, b in zip(range(len(packet)), packet):
                if c % 32 == 0:
                    pcap_packet += '\n{:06x} '.format(int(c / 2))
                elif c % 2 == 0:
                    pcap_packet += ' '
                pcap_packet += b
            packets.append(pcap_packet)
        return packets
