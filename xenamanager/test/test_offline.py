"""
Base class for all Xena package tests.

@author yoram@ignissoft.com
"""

from os import path

from trafficgenerator.tgn_utils import TgnError
from xenamanager.xena_stream import XenaModifierType
from xenamanager.xena_stream import XenaStream
from xenamanager.test.test_base import XenaTestBase


class XenaTestOffline(XenaTestBase):

    def test_inventory(self):
        self.xm.session.inventory()
        stats = {}
        for name, chassis in self.xm.session.chassis_list.items():
            stats[name] = chassis.read_stats()
        print('+++')
        for c_name, chassis in self.xm.session.chassis_list.items():
            print(c_name)
            for m_name, module in chassis.modules.items():
                print(m_name)
                for p_name, _ in module.ports.items():
                    print(p_name)
        print('+++')

    def test_load_config(self):
        #: :type port: xenamanager.xena_port.XenaPort
        port = self.xm.session.reserve_ports([self.port2])[self.port2]
        port.load_config(path.join(path.dirname(__file__), 'configs', 'test_config_1.xpc'))

        assert(len(port.streams) == 2)
        assert(XenaStream.next_tpld_id == 2)

        packet = port.streams[0].get_packet_headers()
        print(packet)
        assert(packet.dst_s == '22:22:22:22:22:11')
        assert(packet.ip.dst_s == '2.2.2.1')
        packet.dst_s = '33:33:33:33:33:33'
        packet.ip.dst_s = '3.3.3.3'
        port.streams[0].set_packet_headers(packet)
        packet = port.streams[0].get_packet_headers()
        print(packet)
        assert(packet.dst_s == '33:33:33:33:33:33')
        assert(packet.ip.dst_s == '3.3.3.3')

        packet = port.streams[1].get_packet_headers()
        print(packet)
        assert(packet.dst_s == '22:22:22:22:22:22')
        assert(packet.ip6.dst_s == '22::22')
        packet.ip6.dst_s = u'33::33'
        port.streams[1].set_packet_headers(packet)
        packet = port.streams[1].get_packet_headers()
        print(packet)
        assert(packet.ip6.dst_s == '33::33')

        assert(len(port.streams[0].modifiers) == 1)
        #: :type modifier1: xenamanager.xena_strea.XenaModifier
        modifier1 = port.streams[0].modifiers[4]
        assert(modifier1.min_val == 0)
        print(modifier1)
        #: :type modifier2: xenamanager.xena_strea.XenaModifier
        modifier2 = port.streams[0].add_modifier(position=12)
        assert(len(port.streams[0].modifiers) == 2)
        modifier2.get()
        assert(modifier2.position == 12)
        print(modifier2)
        print(port.streams[0].modifiers)

        port.streams[0].remove_modifier(4)
        assert(port.streams[0].modifiers[12].max_val == 65535)

    def test_extended_modifiers(self):
        try:
            port = self.xm.session.reserve_ports([self.port3])[self.port3]
        except TgnError as e:
            self.skipTest('Skip test - ' + str(e))
        port.load_config(path.join(path.dirname(__file__), 'configs', 'test_config_100G.xpc'))

        assert(len(port.streams[0].modifiers) == 1)
        #: :type modifier1: xenamanager.xena_strea.XenaModifier
        modifier1 = port.streams[0].modifiers[4]
        assert(modifier1.min_val == 0)
        print(modifier1)
        #: :type modifier2: xenamanager.xena_strea.XenaModifier
        modifier2 = port.streams[0].add_modifier(position=12, m_type=XenaModifierType.extended)
        assert(len(port.streams[0].modifiers) == 2)
        modifier2.get()
        assert(modifier2.position == 12)
        print(modifier2)
        print(port.streams[0].modifiers)

        port.streams[0].remove_modifier(4)
        assert(port.streams[0].modifiers[12].max_val == 65535)

    def test_build_config(self):

        #: :type port: xenamanager.xena_port.XenaPort
        port = self.xm.session.reserve_ports([self.port1], force=False, reset=True)[self.port1]

        assert(XenaStream.next_tpld_id == 0)
        assert(len(port.streams) == 0)
        assert(port.get_attribute('ps_indices') == '')

        stream = port.add_stream('first stream')
        assert(stream.get_attribute('ps_comment')[1:-1] == 'first stream')
        assert(stream.get_attribute('ps_tpldid') == '0')
        assert(XenaStream.next_tpld_id == 1)
        assert(len(port.streams) == 1)

        stream = port.add_stream(tpld_id=7)
        assert(stream.get_attribute('ps_tpldid') == '7')
        assert(XenaStream.next_tpld_id == 8)
        assert(len(port.streams) == 2)

        port.remove_stream(0)
        assert(len(port.streams) == 1)
        assert(port.streams.get(1))
        assert(port.get_attribute('ps_indices').split()[0] == '1')

        port.save_config(path.join(path.dirname(__file__), 'configs', 'save_config.xpc'))
