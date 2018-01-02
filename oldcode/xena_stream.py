
import re


import XenaModifier

from xenamanager.xena_object import XenaObject


class XenaStream(XenaObject):

    def __init__(self, location, parent):
        super(self.__class__, self).__init__(objType='stream', index=location, parent=parent)

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
        return self.read_stat(['bps', 'pps', 'bytes', 'packets'], 'pt_stream')

    #
    # Old code.
    #

    def set_stream_on(self):
        return self.__sendCommand('ps_enable', 'on')

    def set_stream_off(self):
        return self.__sendCommand('ps_enable', 'off')

    def set_stream_suppress(self):
        return self.__sendCommand('ps_enable', 'suppress')

    def get_stream_status(self):
        reply = self.__sendQuery('ps_enable', '?')
        return reply.split()[-1]

    def set_packet_limit(self, count):
        return self.__sendCommand('ps_packetlimit', '%d' % count)

    def disable_packet_limit(self):
        return self.__sendCommand('ps_packetlimit', '-1')

    def set_rate_fraction(self, fraction=1000000):
        return self.__sendCommand('ps_ratefraction', '%d' % fraction)

    def set_rate_pps(self, pps):
        return self.__sendCommand('ps_ratepps', '%d' % pps)

    def get_rate_pps(self):
        reply = self.__sendQuery('ps_ratepps', '?')
        return reply.split()[-1]

    def set_packet_header(self, header):
        return self.__sendCommand('ps_packetheader', '%s' % header)

    def set_packet_protocol(self, seg1, seg2='', seg3='', seg4='', seg5=''):
        seg_str = "%s" % seg1
        if seg2:
            seg_str += ' %s' % seg2
            if seg3:
                seg_str += ' %s' % seg3
                if seg4:
                    seg_str += ' %s' % seg4
                    if seg5:
                        seg_str += ' %s' % seg5
        return self.__sendCommand('ps_headerprotocol', '%s' % seg_str)

    def set_packet_length_fixed(self, min_len, max_len):
        cmd_str = "fixed %d %d" % (min_len, max_len)
        return self.__sendCommand('ps_packetlength', cmd_str)

    def set_packet_length_incrementing(self, min_len, max_len):
        cmd_str = "incrementing %d %d" % (min_len, max_len)
        return self.__sendCommand('ps_packetlength', cmd_str)

    def set_packet_length_butterfly(self, min_len, max_len):
        cmd_str = "butterfly %d %d" % (min_len, max_len)
        return self.__sendCommand('ps_packetlength', cmd_str)

    def set_packet_length_random(self, min_len, max_len):
        cmd_str = "random %d %d" % (min_len, max_len)
        return self.__sendCommand('ps_packetlength', cmd_str)

    def set_packet_length_mix(self, min_len, max_len):
        cmd_str = "mix %d %d" % (min_len, max_len)
        return self.__sendCommand('ps_packetlength', cmd_str)

    def set_packet_payload_pattern(self, hexdata):
        cmd_str = "pattern %s" % hexdata
        return self.__sendCommand('ps_payload', cmd_str)

    def set_packet_payload_incrementing(self, hexdata):
        cmd_str = "incrementing %s" % hexdata
        return self.__sendCommand('ps_payload', cmd_str)

    def set_packet_payload_prbs(self, hexdata):
        cmd_str = "prbs %s" % hexdata
        return self.__sendCommand('ps_payload', cmd_str)

    def disable_test_payload_id(self):
        return self.__sendCommand('ps_tpldid', -1)

    def set_test_payload_id(self, tpldid):
        return self.__sendCommand('ps_tpldid', '%d' % tpldid)

    def set_frame_csum_on(self):
        return self.__sendCommand('ps_insertfcs', 'on')

    def set_frame_csum_off(self):
        return self.__sendCommand('ps_insertfcs', 'off')

    def add_modifier(self):
        mid = len(self.modifiers.keys())
        tmids = mid + 1
        if not self.__sendCommand('ps_modifiercount', "%d" % tmids):
            self.logger.error("Failed to create a modifier")
            return -1

        modnew = XenaModifier.XenaModifier(self.xsocket, self.port, self, mid)
        self.modifiers[mid] = modnew
        return modnew

    def get_modifier(self, module, modifier_id):
        if modifier_id in self.modifiers:
            return self.modifiers[modifier_id]
        return None

    def remove_modifier(self, modifier_id):
        self.logger.error("Operation not supported")
        return -1
