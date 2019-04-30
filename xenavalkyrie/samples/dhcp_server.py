"""
Load multi stream configuration and run streams one by one, save results and first packet of each stream in a file.

Setup:
Two Xena ports connected back to back.

@author yoram@ignissoft.com
"""

import sys
import logging
import time
import binascii
import socket
from pypacker.layer12.ethernet import Ethernet

from trafficgenerator.tgn_utils import ApiType
from xenavalkyrie.xena_app import init_xena
from xenavalkyrie.xena_port import XenaCaptureBufferType

wireshark_path = '/usr/bin'

api = ApiType.socket
chassis = '176.22.65.117'
client_location = chassis + '/' + '0/0'
server_location = chassis + '/' + '0/1'
owner = 'dhcp'
client_config = 'dhcp_client.xpc'
server_config = 'dhcp_server.xpc'
cap_file = 'packets.txt'
results_file = 'results.txt'
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


def act_dhcp(server_location, client_location, server_ip, client_ip, subnet_mask, router_ip):

    global ports

    # Reserve ports
    ports = xm.session.reserve_ports([client_location, server_location], force=True, reset=False)
    server = ports[server_location]
    client = ports[client_location]
    server.wait_for_up(16)
    client.wait_for_up(16)

    # Load configuration on port-0.
    # client.load_config(client_config)
    # server.load_config(server_config)

    # Send Discover
    client.streams[0].set_attributes(PS_ENABLE='ON')
    client.streams[1].set_attributes(PS_ENABLE='OFF')
    server.start_capture()
    client.start_traffic()
    while not server.capture.packets:
        time.sleep(0.1)
    server.stop_capture()

    # At this point we know we have received Discover
    packet = server.capture.get_packets(to_index=1, cap_type=XenaCaptureBufferType.raw)[0]
    discover = Ethernet(binascii.unhexlify(packet))
    print(discover)

    # Send Offer packet.
    server.streams[0].set_attributes(PS_ENABLE='ON')
    server.streams[1].set_attributes(PS_ENABLE='OFF')
    eth = server.streams[0].get_packet_headers()
    ip = eth.ip
    ip.src_s = server_ip
    ip.dst_s = client_ip
    dhcp = eth.ip.udp.dhcp
    dhcp.yiaddr_s = client_ip
    dhcp.opts[1].body_bytes = socket.inet_aton(server_ip)
    dhcp.opts[3].body_bytes = socket.inet_aton(subnet_mask)
    dhcp.opts[4].body_bytes = socket.inet_aton(router_ip)
    server.streams[0].set_packet_headers(eth)
    server.start_traffic()

    # Send Request
    client.streams[0].set_attributes(PS_ENABLE='OFF')
    client.streams[1].set_attributes(PS_ENABLE='ON')
    server.start_capture()
    client.start_traffic()
    while not server.capture.packets:
        time.sleep(0.1)
    server.stop_capture()

    # Send Ack packet.
    server.streams[0].set_attributes(PS_ENABLE='OFF')
    server.streams[1].set_attributes(PS_ENABLE='ON')
    eth = server.streams[1].get_packet_headers()
    ip = eth.ip
    ip.src_s = server_ip
    ip.dst_s = client_ip
    dhcp = ip.udp.dhcp
    dhcp.yiaddr_s = client_ip
    dhcp.opts[1].body_bytes = socket.inet_aton(server_ip)
    dhcp.opts[3].body_bytes = socket.inet_aton(subnet_mask)
    dhcp.opts[4].body_bytes = socket.inet_aton(router_ip)
    server.streams[1].set_packet_headers(eth)
    server.start_traffic()

    # Release ports.
    xm.session.release_ports()


def run_all():
    connect()
    act_dhcp(server_location, client_location, '10.10.10.1', '10.10.10.10', '255.255.255.0', '10.10.10.1')
    disconnect()


if __name__ == '__main__':
    run_all()
