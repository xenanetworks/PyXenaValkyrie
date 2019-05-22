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

api = ApiType.socket
chassis = '10.5.216.105'
server_location = chassis + '/' + '0/7'
owner = 'dhcp'
server_config = 'dhcp_server.xpc'


logger = logger = logging.getLogger()
xm = None
ports = {}


def connect():
    """ Create Xena manager object and connect to chassis. """

    global xm

    # Xena manager requires standard logger. To log all low level CLI commands set DEBUG level.
    formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)d %(message)s',
                                  datefmt='%H:%M:%S')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Create XenaApp object and connect to chassis.
    xm = init_xena(api, logger, owner, chassis)
    xm.session.add_chassis(chassis)


def disconnect():
    """ Disconnect from chassis. """

    xm.session.disconnect()


def act_dhcp(server_port, server_ip, client_ip, subnet_mask, router_ip, dns_ip):

    global ports

    # Reserve ports
    ports = xm.session.reserve_ports([server_port], force=True, reset=False)
    server = ports[server_location]
    # server.wait_for_up(16)

    # Load configuration on port-0.
    server.load_config(server_config)

    # Prep whatever possible in advance.
    offer = server.streams[0].get_packet_headers()
    offer.ip.src_s = server_ip
    offer.ip.dst_s = '255.255.255.255'
    offer.ip.udp.dhcp.yiaddr_s = client_ip
    offer.ip.udp.dhcp.opts[1].body_bytes = socket.inet_aton(server_ip)
    offer.ip.udp.dhcp.opts[3].body_bytes = socket.inet_aton(subnet_mask)
    offer.ip.udp.dhcp.opts[4].body_bytes = socket.inet_aton(router_ip)
    offer.ip.udp.dhcp.opts[5].body_bytes = socket.inet_aton(dns_ip)
    ack = server.streams[1].get_packet_headers()
    ack.ip.src_s = server_ip
    ack.ip.dst_s = client_ip
    ack.ip.udp.dhcp.yiaddr_s = client_ip
    ack.ip.udp.dhcp.opts[1].body_bytes = socket.inet_aton(server_ip)
    ack.ip.udp.dhcp.opts[3].body_bytes = socket.inet_aton(subnet_mask)
    ack.ip.udp.dhcp.opts[4].body_bytes = socket.inet_aton(router_ip)
    ack.ip.udp.dhcp.opts[5].body_bytes = socket.inet_aton(router_ip)

    print("Ready to receive DHCP request\n")

    # Wait for Discover
    server.start_capture()
    while not server.capture.packets:
        time.sleep(0.01)
    server.stop_capture()

    # At this point we know we have received Discover
    packet = server.capture.get_packets(cap_type=XenaCaptureBufferType.raw)[-1]
    discover = Ethernet(binascii.unhexlify(packet))
    client_mac = discover.src_s
    chaddr = binascii.unhexlify(client_mac.replace(':', '') + '000000000000')
    transaction_id = discover.ip.udp.dhcp.xid

    # Send Offer packet.
    server.streams[0].set_attributes(PS_ENABLE='ON')
    server.streams[1].set_attributes(PS_ENABLE='OFF')
    offer.dst_s = client_mac
    offer.ip.udp.dhcp.chaddr = chaddr
    offer.ip.udp.dhcp.xid = transaction_id
    server.streams[0].set_packet_headers(offer, udp_checksum=True)
    server.start_traffic()

    # Wait for Request
    server.start_capture()
    while not server.capture.packets:
        time.sleep(0.01)
    server.stop_capture()
    server.stop_traffic()

    # At this point we know we have received Request

    # Send Ack packet.
    server.streams[0].set_attributes(PS_ENABLE='OFF')
    server.streams[1].set_attributes(PS_ENABLE='ON')
    ack.dst_s = client_mac
    ack.ip.udp.dhcp.chaddr = chaddr
    ack.ip.udp.dhcp.xid = transaction_id
    server.streams[1].set_packet_headers(ack, udp_checksum=True)
    server.start_traffic()

    # Release ports.
    xm.session.release_ports()


def run_all():
    connect()
    act_dhcp(server_location, '192.168.1.138', '192.168.1.10', '255.255.255.0', '192.168.1.138', '192.168.1.138')
    disconnect()


if __name__ == '__main__':
    run_all()
