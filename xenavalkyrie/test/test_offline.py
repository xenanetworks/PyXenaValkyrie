"""
Base class for all Xena package tests.

@author yoram@ignissoft.com
"""

from os import path
import pytest
import requests

from trafficgenerator.tgn_utils import ApiType, is_local_host
from xenavalkyrie.xena_stream import XenaModifierType, XenaModifierAction
from xenavalkyrie.xena_stream import XenaStream
from xenavalkyrie.test.test_base import TestXenaBase


class TestXenaOffline(TestXenaBase):

    def test_inventory(self):
        self.xm.session.inventory()
        print('+++')
        for c_name, chassis in self.xm.session.chassis_list.items():
            print(c_name)
            for m_name, module in chassis.modules.items():
                print('\tmodule {}'.format(m_name))
                for p_name, _ in module.ports.items():
                    print('\t\tport {}'.format(p_name))
        print('+++')

        save_config = path.join(path.dirname(__file__), 'configs', 'save_config.xmc')
        self.xm.session.chassis_list.values()[0].save_config(save_config)

    def test_load_config(self):
        #: :type port: xenavalkyrie.xena_port.XenaPort
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
        assert(port.streams[0].modifiers[0].action == XenaModifierAction.increment)
        print(port.streams[0].modifiers[0].get_attributes())
        assert(len(port.streams[1].modifiers) == 1)
        assert(port.streams[1].modifiers[0].action == XenaModifierAction.random)
        print(port.streams[1].modifiers[0].get_attributes())
        #: :type modifier1: xenavalkyrie.xena_strea.XenaModifier
        modifier1 = port.streams[0].modifiers[0]
        assert(modifier1.min_val == 0)
        print(modifier1)
        #: :type modifier2: xenavalkyrie.xena_strea.XenaModifier
        modifier2 = port.streams[0].add_modifier(position=12)
        assert(len(port.streams[0].modifiers) == 2)
        assert(modifier2.position == 12)
        print(modifier2)
        print(port.streams[0].modifiers)

        port.streams[0].remove_modifier(0)
        assert(port.streams[0].modifiers[0].max_val == 65535)

    def test_extended_modifiers(self):
        try:
            port = self.xm.session.reserve_ports([self.port3])[self.port3]
        except Exception as e:
            pytest.skip('Skip test - ' + str(e))
        port.load_config(path.join(path.dirname(__file__), 'configs', 'test_config_100G.xpc'))

        assert(len(port.streams[0].modifiers) == 1)
        #: :type modifier1: xenavalkyrie.xena_strea.XenaModifier
        modifier1 = port.streams[0].modifiers[0]
        assert(modifier1.min_val == 0)
        print(modifier1)
        #: :type modifier2: xenavalkyrie.xena_strea.XenaXModifier
        modifier2 = port.streams[0].add_modifier(m_type=XenaModifierType.extended, position=12)
        assert(len(port.streams[0].modifiers) == 1)
        assert(len(port.streams[0].xmodifiers) == 1)
        assert(modifier2.position == 12)
        print(modifier2)

        port.streams[0].remove_modifier(0)
        assert(len(port.streams[0].modifiers) == 0)
        assert(len(port.streams[0].xmodifiers) == 1)
        port.streams[0].remove_modifier(0, m_type=XenaModifierType.extended)
        assert(len(port.streams[0].xmodifiers) == 0)

    def test_build_config(self):

        #: :type port: xenavalkyrie.xena_port.XenaPort
        port = self.xm.session.reserve_ports([self.port1], force=False, reset=True)[self.port1]

        assert(XenaStream.next_tpld_id == 0)
        assert(len(port.streams) == 0)
        assert(port.get_attribute('ps_indices') == '')

        stream = port.add_stream('first stream')
        assert(stream.get_attribute('ps_comment') == 'first stream')
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

    def test_rest_server(self):

        if self.api == ApiType.rest:
            pytest.skip('Skip test - REST API')

        if is_local_host(self.server_ip):
            pytest.skip('Skip test - localhost')

        #: :type chassis: xenavalkyrie.xena_app.XenaChassis
        chassis = self.xm.session.chassis_list[self.chassis]
        chassis.reserve()

        assert(int(chassis.get_attribute('c_restport')) == self.server_port)
        assert(chassis.get_attribute('c_reststatus').lower() == 'service_on')
        assert(chassis.get_attribute('c_restenable').lower() == 'on')
        base_url = 'http://{}:{}'.format(self.server_ip, self.server_port)
        requests.get(base_url)
        chassis.set_attributes(c_restport=self.server_port + 10)
        chassis.set_attributes(c_restcontrol='restart')
        assert(chassis.get_attribute('c_reststatus').lower() == 'service_on')
        assert(int(chassis.get_attribute('c_restport')) == self.server_port + 10)
        base_url = 'http://{}:{}'.format(self.server_ip, self.server_port + 10)
        requests.get(base_url)
        chassis.set_attributes(c_restport=self.server_port)
        chassis.set_attributes(c_restcontrol='stop')
        assert(chassis.get_attribute('c_reststatus').lower() == 'service_off')
        base_url = 'http://{}:{}'.format(self.server_ip, self.server_port)
        with pytest.raises(Exception) as _:
            requests.get(base_url)
        chassis.set_attributes(c_restcontrol='start')
        assert(chassis.get_attribute('c_reststatus').lower() == 'service_on')
        requests.get(base_url)

        chassis.set_attributes(c_restenable='off')
        assert(chassis.get_attribute('c_restenable').lower() == 'off')
        chassis.shutdown(restart=True, wait=True)
        assert(chassis.get_attribute('c_restenable').lower() == 'off')
        with pytest.raises(Exception) as _:
            requests.get(base_url)
        chassis.reserve()
        chassis.set_attributes(c_restenable='on')
        assert(chassis.get_attribute('c_restenable').lower() == 'on')
        chassis.shutdown(restart=True, wait=True)
        assert(chassis.get_attribute('c_restenable').lower() == 'on')
        requests.get(base_url)
