
import re
from collections import OrderedDict

from xenamanager.xena_object import XenaObject
from xenamanager.xena_stream import XenaStream


class XenaPort(XenaObject):

    stats_captions = {'pr_pfcstats': ['total', 'CoS 0', 'CoS 1', 'CoS 2', 'CoS 3', 'CoS 4', 'CoS 5', 'CoS 6', 'CoS 7'],
                      'pr_total': ['bps', 'pps', 'bytes', 'packets'],
                      'pr_notpld': ['bps', 'pps', 'bytes', 'packets'],
                      'pr_extra': ['fcserrors', 'pauseframes', 'arprequests', 'arpreplies', 'pingrequests',
                                   'pingreplies', 'gapcount', 'gapduration'],
                      'pt_total': ['bps', 'pps', 'bytes', 'packets'],
                      'pt_extra': ['arprequests', 'arpreplies', 'pingrequests', 'pingreplies', 'injectedfcs',
                                   'injectedseq', 'injectedmis', 'injectedint', 'injectedtid', 'training'],
                      'pt_notpld': ['bps', 'pps', 'bytes', 'packets']}

    def __init__(self, location, parent):
        super(self.__class__, self).__init__(objType='port', index=location, parent=parent)
        self._data['name'] = '{}/{}'.format(parent.name, location)

    def inventory(self):
        self.p_info = self.get_attributes('p_info')

    def reserve(self, force):
        """ Reserve port.

        XenaManager-2G -> Reserve/Relinquish Port.

        :param force: True - take forcefully, False - fail if port is reserved by other user
        """

        if self.get_attribute('p_reservation') == 'RESERVED_BY_YOU':
            return
        if force:
            self.relinquish()
        self.send_command('p_reservation reserve')

    def relinquish(self):
        if self.get_attribute('p_reservation') != 'RELEASED':
            self.send_command('p_reservation relinquish')

    def release(self):
        return self.send_command('p_reservation release')

    def reset(self):
        return self.send_command('p_reset')

    def wait_for_up(self, timeout=40):
        self.wait_for_states('P_RECEIVESYNC', timeout, 'IN_SYNC')

    def load_config(self, config_file_name):
        """ Load configuration file from xpc file.

        :param config_file_name: full path to the configuration file.
        """

        with open(config_file_name) as f:
            commands = f.read().splitlines()

        for command in commands:
            if not command.startswith(';'):
                self.send_command(command)

        for index in self.send_command_return('ps_indices', '?').split():
            XenaStream(location='{}/{}'.format(self.ref, index), parent=self)

    #
    # Operations.
    #

    def start_traffic(self):
        """

        Capture -> Start Capture
        """
        self.send_command('p_capture', 'on')

    def stop_traffic(self):
        """

        Capture -> Stop Capture
        """
        self.send_command('p_capture', 'on')

    def start_capture(self):
        """

        Capture -> Start Capture
        """
        self.send_command('p_capture', 'on')

    def stop_capture(self):
        """

        Capture -> Stop Capture
        """
        self.send_command('p_capture', 'on')

    #
    # Statistics.
    #

    def clear_stats(self):
        self.send_command('pt_clear')
        self.send_command('pr_clear')

    def read_port_stats(self):
        stats_with_captions = OrderedDict()
        for stat_name in self.stats_captions.keys():
            stats_with_captions[stat_name] = self.read_stat(self.stats_captions[stat_name], stat_name)
        return stats_with_captions

    def read_stream_stats(self):
        stream_stats = OrderedDict()
        for stream in self.streams.values():
            stream_stats[stream] = stream.read_stats()
        return stream_stats

    def read_tpld_stats(self):
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
        for tpld in self.parent.get_objects_by_type('tpld'):
            tpld.del_object_from_parent()
        for tpld in self.get_attribute('pr_tplds').split():
            XenaTpld(location='{}/{}'.format(self.ref, tpld), parent=self.parent).read_stats()
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

    def __init__(self, location, parent):
        super(self.__class__, self).__init__(objType='tpld', index=location, parent=parent)

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
        stats_with_captions = OrderedDict()
        for stat_name in self.stats_captions.keys():
            stats_with_captions[stat_name] = self.read_stat(self.stats_captions[stat_name], stat_name)
        return stats_with_captions


class XenaCapture(XenaObject):
    """ Represents cappture parameters, correspond to the Capture panel of the XenaManager, and deal with configuration
        of the capture criteria and inspection of the captured data from a port.
    """

    def __init__(self, parent):
        super(self.__class__, self).__init__(objType='capture', index=parent.ref.split('/'), parent=parent)
