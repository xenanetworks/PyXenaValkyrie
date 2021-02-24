"""
Stand alone samples demonstrating Xena package functionality.

Setup:
Two Xena ports connected back to back.

@author yoram@ignissoft.com
"""

from os import path
import sys
import logging

from pypacker import ppcap
from pypacker.layer12.ethernet import Ethernet

from trafficgenerator.tgn_utils import ApiType
from xenavalkyrie.xena_app import init_xena

wireshark_path = '/usr/bin'

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
xm = None


def connect():
    """ Create Xena manager object and connect to chassis. """

    global xm

    # Xena manager requires standard logger. To log all low level CLI commands set DEBUG level.
    logger = logging.getLogger('log')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))

    # Create XenaApp object and connect to chassis.
    xm = init_xena(api, logger, owner, chassis)
    xm.session.add_chassis(chassis)


def disconnect():
    """ Disconnect from chassis. """

    xm.session.disconnect()


def configuration():

    global ports

    ports = xm.session.reserve_ports([port0, port1], True)
    ports[port0].wait_for_up(16)
    ports[port1].wait_for_up(16)

    # Read packet from pcap.
    pcap_packets = []
    with ppcap.Reader(filename='tcp1.pcap') as pcap:
        for ts, buf in pcap:
            eth = Ethernet(buf)
            pcap_packets.append(eth)


    # Write the first packet to Valkyrie as first stream.
    print(f'packet: {pcap_packets[0]}')
    p1_s0 = ports[port1].add_stream('original packet')
    p1_s0.set_packet_headers(pcap_packets[0])

    # Change the MAC address of first packet and write it to Valkyrie as second stream.
    pcap_packets[0].src_s = '11:11:11:11:11:11'
    pcap_packets[0].dst_s = '22:22:22:22:22:22'
    print(f'packet: {pcap_packets[0]}')
    p1_s1 = ports[port1].add_stream('modified packet')
    p1_s1.set_packet_headers(pcap_packets[0])


if __name__ == '__main__':
    connect()
    configuration()
    disconnect()
