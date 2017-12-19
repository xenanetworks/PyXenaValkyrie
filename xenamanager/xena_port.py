
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
        pr_tplds = self.get_attribute('pr_tplds')
        payloads_stats = OrderedDict()
        for tpld in pr_tplds.split():
            payloads_stats[tpld] = XenaTpld(location='{}/{}'.format(self.ref, tpld), parent=self).read_stats()
        return payloads_stats

    @property
    def streams(self):
        """
        :return: dictionary {index: object} of all streams.
        """

        return {int(s.ref.split('/')[-1]): s for s in self.get_objects_by_type('stream')}

    #
    # Old code.
    #

    def set_autoneg_on(self):
        return self.__sendCommand('p_autonegselection on')

    def set_autoneg_off(self):
        return self.__sendCommand('p_autonegselection off')

    def get_autoneg_enabled(self):
        reply = self.__sendQuery('p_autonegselection ?')
        if reply.split()[-1] == 'ON':
            status = True
        else:
            status = False

        self.logger.debug("Port(%s): Got port autoneg: %s", self.port_str(), status)
        return status

    def set_tx_speed_reduction(self, parts_per_million):
        return self.__sendCommand('p_speedreduction %d' % parts_per_million)

    def get_tx_speed_reduction(self):
        reply = self.__sendQuery('p_speedreduction ?')
        ppm = int(reply.split()[-1])
        self.logger.debug("Port(%s): Tx speed reduction: %d", self.port_str(), ppm)
        return ppm

    def set_interframe_gap(self, minbytes=20):
        return self.__sendCommand('p_interframegap %d' % minbytes)

    def get_interframe_gap(self):
        reply = self.__sendQuery('p_interframegap ?')
        gap = int(reply.split()[-1])
        self.logger.debug("Port(%s): Interframe gap: %d", self.port_str(), gap)
        return gap

    def set_macaddr(self, macaddr='04:F4:BC:2F:A9:80'):
        macaddrstr = ''.join(macaddr.split(':'))
        return self.__sendCommand('p_macaddress %s' % macaddrstr)

    def get_macaddr(self):
        reply = self.__sendQuery('p_macaddress ?')
        macstr = int(reply.split()[-1])
        macaddress = "%s:%s:%s:%s:%s:%s" % (macstr[2:4], macstr[4:6],
                                            macstr[6:8], macstr[8:10], macstr[10:12], macstr[12:14])
        self.logger.debug("Port(%s): Mac address: %s", self.port_str(), macaddress)
        return macaddress

    def set_ipaddr(self, ipaddr, subnet, gateway, wild='0.0.0.255'):
        cmd = 'p_ipaddress %s %s %s %s' % (ipaddr, subnet, gateway, wild)
        return self.__sendCommand(cmd)

    def get_ipaddr(self):
        reply = self.__sendQuery('p_ipaddr ?')
        config_list = reply.split()
        wild = config_list[-1]
        gw = config_list[-2]
        subnet = config_list[-3]
        ipaddr = config_list[-4]
        self.logger.debug("Port(%s): Port ip config: %s, %s, %s, %s",
                          self.port_str(), ipaddr, subnet, gw, wild)
        return (ipaddr, subnet, gw, wild)

    def set_arpreply_on(self):
        return self.__sendCommand('p_arpreply on')

    def set_arpreply_off(self):
        return self.__sendCommand('p_arpreply off')

    def get_arpreply_enabled(self):
        reply = self.__sendQuery('p_arpreply ?')
        if reply.split()[-1] == 'ON':
            status = True
        else:
            status = False

        self.logger.debug("Port(%s): ARP reply enabled: %s", self.port_str(), status)
        return status

    def set_pingreply_on(self):
        return self.__sendCommand('p_pingreply on')

    def set_pingreply_off(self):
        return self.__sendCommand('p_pingreply off')

    def get_pingreply_enabled(self):
        reply = self.__sendQuery('p_pingreply ?')
        if reply.split()[-1] == 'ON':
            status = True
        else:
            status = False

        self.logger.debug("Port(%s): PING reply enabled: %s", self.port_str(), status)
        return status

    def set_pause_frames_on(self):
        return self.__sendCommand('p_pause on')

    def set_pause_frames_off(self):
        return self.__sendCommand('p_pause off')

    def get_pause_frames_enabled(self):
        reply = self.__sendQuery('p_pause ?')
        if reply.split()[-1] == 'ON':
            status = True
        else:
            status = False

        self.logger.debug("Port(%s): Pause frames is enabled: %s", self.port_str(), status)
        return status

    def set_extra_csum_on(self):
        return self.__sendCommand('p_checksum on')

    def set_extra_csum_off(self):
        return self.__sendCommand('p_checksum off')

    def get_extra_csum_enabled(self):
        reply = self.__sendQuery('p_checksum ?')
        if reply.split()[-1] == 'ON':
            status = True
        else:
            status = False

        self.logger.debug("Port(%s): Extra checksum is enabled: %s", self.port_str(), status)
        return status

    def set_tx_enabled_on(self):
        return self.__sendCommand('p_txenable on')

    def set_tx_enabled_off(self):
        return self.__sendCommand('p_txenable off')

    def set_txmode_normal(self):
        return self.__sendCommand('p_txmode normal')

    def set_txmode_strictuniform(self):
        return self.__sendCommand('p_txmode strictuniform')

    def set_txmode_sequential(self):
        return self.__sendCommand('p_txmode sequential')

    def get_txmode_status(self):
        reply = self.__sendQuery('p_txmode ?')
        status = reply.split()[-1]
        self.logger.debug("Port(%s): TX mode: %s", self.port_str(), status)
        return status

    def get_tx_enabled_status(self):
        reply = self.__sendQuery('p_txenable ?')
        if reply.split()[-1] == 'ON':
            status = True
        else:
            status = False

        self.logger.debug("Port(%s): Transmitter is enabled: %s", self.port_str(),
                          status)
        return status

    def set_tx_time_limit_ms(self, microsecs):
        return self.__sendCommand('p_txtimelimit %d' % microsecs)

    def get_tx_time_limit_ms(self):
        reply = self.__sendQuery('p_txtimelimit ?')
        limit = int(reply.split()[-1])
        self.logger.debug("Port(%s): TX time limit: %d", self.port_str(), limit)
        return limit

    def get_tx_elapsed_time(self):
        elapsed = 0
        if self.get_traffic_status():
            reply = self.__sendQuery('p_txtime ?')
            elapsed = int(reply.split()[-1])
            self.logger.debug("Port(%s): Transmitting for %s usec", self.port_str(), elapsed)
        else:
            self.logger.error("Port(%s): Elapsed time on a stopped port", self.port_str())
        return elapsed

    def add_stream(self, sid):
        if sid in self.streams:
            self.logger.error("Adding duplicated stream")
            return

        if self.__sendCommand('ps_create [%s]' % sid):
            stream_new = XenaStream(self.xsocket, self, sid)
            self.streams[sid] = stream_new
            return stream_new

        return

    def del_stream(self, sid):
        stream_del = self.streams.pop(sid)
        del stream_del
        return self.__sendCommand('ps_delete [%s]' % sid)


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
