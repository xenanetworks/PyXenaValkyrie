"""
Stand alone samples demonstrating Xena package functionality.

Setup:
Two Xena ports connected back to back.

@author yoram@ignissoft.com
"""

import binascii
import json
import logging
import sys
from os import path
from typing import Optional

from pypacker.layer12.ethernet import Ethernet, Dot1Q
from pypacker.layer3.ip6 import IP6
from pypacker.layer4.tcp import TCP

from trafficgenerator.tgn_utils import ApiType
from xenavalkyrie.xena_app import init_xena, XenaApp
from xenavalkyrie.xena_port import XenaCaptureBufferType, XenaStreamState
from xenavalkyrie.xena_statistics_view import XenaPortsStats, XenaStreamsStats, XenaTpldsStats
from xenavalkyrie.xena_tshark import Tshark, TsharkAnalyzer

wireshark_path = 'C:/Program Files/Wireshark'

api = ApiType.socket
chassis = '176.22.65.117'
port0 = chassis + '/' + '0/0'
port1 = chassis + '/' + '0/1'
owner = 'pyxenavalkyrie-sample'
config0 = path.join(path.dirname(__file__), 'test_config_1.xpc')
save_config = path.join(path.dirname(__file__), 'save_config.xpc')
pcap_file = path.join(path.dirname(__file__), 'xena_cap.pcap')
ports = {}

#: :type xm: xenavalkyrie.xena_app.XenaApp
xm: XenaApp = Optional[None]

# Xena manager requires standard logger. To log all low level CLI commands set DEBUG level.
logger = logging.getLogger('log')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


def connect():
    """ Create Xena manager object and connect to chassis. """

    global xm

    # Create XenaApp object and connect to chassis.
    xm = init_xena(api, logger, owner, chassis)
    xm.session.add_chassis(chassis)


def disconnect():
    """ Disconnect from chassis. """

    xm.session.disconnect()


def inventory():
    """ Get inventory of all chassis. """

    xm.session.inventory()
    print('+++')
    for c_name, chassis in xm.session.chassis_list.items():
        print('chassis ' + c_name)
        for m_name, module in chassis.modules.items():
            print('\tmodule ' + str(m_name))
            print(json.dumps(module.get_attributes(), indent=2))
            for p_name, port in module.ports.items():
                print('\t\tport ' + str(p_name))
                for s_name, stream in port.streams.items():
                    print('\t\t\tstream ' + str(s_name))
                    print(f'Attr {json.dumps(stream.get_attributes(), indent=2)}')
    print('+++')


def configuration():
    """ Reserve ports.
        Wait for ports up.
        Load configuration on one port.
        Build configuration on the second port.
    """

    global ports

    #: :type header: pypacker.layer12.ethernet
    #: :type p0_s0: xenavalkyrie.xena_stream.XenaStream
    #: :type p1_s0: xenavalkyrie.xena_stream.XenaStream
    #: :type modifier: xenavalkyrie.xena_strea.XenaModifier

    ports = xm.session.reserve_ports([port0, port1], True)
    ports[port0].wait_for_up(16)
    ports[port1].wait_for_up(16)

    # Load configuration on port-0.
    ports[port0].load_config(config0)

    # Get port-0/stream-0 object.
    p0_s0 = ports[port0].streams[0]

    # Get Multi-parameter query with get_attributes which returns all attributes values as dict.
    ps_config = p0_s0.get_attributes()
    print('{} info:\n{}'.format(p0_s0.name, json.dumps(ps_config, indent=1)))

    # Get packet headers.
    headers = p0_s0.get_packet_headers()
    print('{} headers:\n{}'.format(p0_s0.name, headers))
    # Access any header and field by name with nice string representation.
    print('{} MAC SRC: {}'.format(p0_s0.name, headers.src_s))
    print('{} VLAN ID: {}'.format(p0_s0.name, headers.vlan[0].vid))
    print('{} IP DST: {}'.format(p0_s0.name, headers.upper_layer.dst_s))

    # Add stream on port-1
    p1_s0 = ports[port1].add_stream('new stream')

    # Set ps_packetlimit and ps_ratepps with set_attributes which sets list of attributes.
    p1_s0.set_attributes(ps_packetlimit=800, ps_ratepps=100)

    # Get single parameter query with get_attribute which returns the attribute value as str.
    ps_packetlimit = p1_s0.get_attribute('ps_packetlimit')
    ps_ratepps = p1_s0.get_attribute('ps_ratepps')
    print('{} info:\nps_packetlimit: {}\nps_ratepps: {}'.format(p1_s0.name, ps_packetlimit, ps_ratepps))

    p1_s0.set_attributes(ps_packetlimit=80, ps_ratepps=10)

    # Set headers - all fields can be set with the constructor or by direct access after creation.
    eth = Ethernet(src_s='22:22:22:22:22:22')
    eth.dst_s = '11:11:11:11:11:11'
    vlan = Dot1Q(vid=17, prio=3)
    eth.vlan.append(vlan)
    # In order to add header simply concatenate it.
    ip6 = IP6()
    ip6.src_s = '128::01'
    ip6.dst_s = '128::02'
    tcp = TCP()
    tcp.sport = 200
    tcp.dport = 300
    headers = eth + ip6 + tcp
    p1_s0.set_packet_headers(headers)

    # Add modifier - all parameters can be set with the constructor or by direct access after creation.
    modifier = p1_s0.add_modifier(position=4)
    modifier.min_val = 100
    modifier.max_val = 200

    # Save new configuration.
    ports[port1].save_config(save_config)


def traffic():
    """ Run traffic.
        Get statistics.
        Get capture.
    """

    # Run traffic with capture on all ports.
    xm.session.clear_stats()
    xm.session.start_capture()
    xm.session.start_traffic(blocking=True)
    xm.session.stop_capture()

    # Get port level statistics.
    ports_stats = XenaPortsStats(xm.session)
    ports_stats.read_stats()
    print(ports_stats.statistics.dumps())

    # Get stream level statistics.
    # For each stream the returned dictionary includes the TX statistics and the associated TPLD statistics.
    streams_stats = XenaStreamsStats(xm.session)
    streams_stats.read_stats()
    print(streams_stats.statistics.dumps())

    # Get TPLD level statistics.
    tplds_stats = XenaTpldsStats(xm.session)
    tplds_stats.read_stats()
    print(tplds_stats.statistics.dumps())

    # Run traffic on one port and capture on the second port.
    xm.session.clear_stats()
    ports[port0].start_capture()
    ports[port1].start_traffic(blocking=True)
    ports[port0].stop_capture()

    # Get individual port statistics.
    print(json.dumps(ports[port0].read_port_stats(), indent=1))

    # Get individual stream statistics.
    print(json.dumps(ports[port0].streams[0].read_stats(), indent=1))

    # Get first two captured packets in raw format - note that MAC address changed due to modifier.
    packets = ports[port0].capture.get_packets(to_index=2, cap_type=XenaCaptureBufferType.raw)
    for packet in packets:
        packet = Ethernet(binascii.unhexlify(packet))
        print(packet.dst_s)

    # Get first two packets in wireshark text format.
    packets = ports[port0].capture.get_packets(from_index=10, to_index=12)
    for packet in packets:
        print(packet)

    # Analyze capture buffer with tshark.
    tshark = Tshark(wireshark_path)
    packets = ports[port0].capture.get_packets(cap_type=XenaCaptureBufferType.pcap,
                                               file_name=pcap_file, tshark=tshark)
    analyser = TsharkAnalyzer()
    analyser.add_field('ip.src')
    analyser.add_field('ip.dst')
    fields = tshark.analyze(pcap_file, analyser)
    print(len(fields))
    analyser.set_read_filter('eth.dst == 11:11:11:11:00:11')
    fields = tshark.analyze(pcap_file, analyser)
    print(len(fields))


def run_all():
    connect()
    inventory()
    configuration()
    traffic()
    disconnect()


if __name__ == '__main__':
    run_all()
