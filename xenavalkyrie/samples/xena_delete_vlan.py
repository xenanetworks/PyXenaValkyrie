"""
Stand alone samples demonstrating Xena package functionality.

Setup:
Two Xena ports connected back to back.

@author yoram@ignissoft.com
"""

from os import path
import sys
import logging

from pypacker.layer12.ethernet import Dot1Q

from trafficgenerator.tgn_utils import ApiType
from xenavalkyrie.xena_app import init_xena

api = ApiType.socket
chassis = '176.22.65.117'
port0 = chassis + '/' + '0/0'
owner = 'delete-vlan-script'
config0 = path.join(path.dirname(__file__), 'test_config_1.xpc')
save_config = path.join(path.dirname(__file__), 'save_config.xpc')
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
    """ Reserve ports.
        Wait for ports up.
        Load configuration on one port.
        Build configuration on the second port.
    """

    global ports

    ports = xm.session.reserve_ports([port0], True)

    # Load configuration on port-0.
    ports[port0].load_config(config0)

    # Get port-0/stream-0 object.
    stream0 = ports[port0].streams[0]
    stream1 = ports[port0].streams[1]

    # Get packet headers.
    headers0 = stream0.get_packet_headers()
    print('{} headers:\n{}'.format(stream0.name, headers0))
    print('{} MAC SRC: {}'.format(stream0.name, headers0.src_s))
    print('{} VLAN ID: {}'.format(stream0.name, headers0.vlan[0].vid))
    print('{} IP DST: {}'.format(stream0.name, headers0.upper_layer.dst_s))

    headers0.vlan[0].vid = 117
    stream0.set_packet_headers(headers0)

    headers1 = stream1.get_packet_headers()
    assert len(headers1.vlan) == 2
    print('{} headers:\n{}'.format(stream1.name, headers1))
    print('{} MAC SRC: {}'.format(stream1.name, headers1.src_s))
    print('{} VLAN ID: {}'.format(stream1.name, headers1.vlan[0].vid))
    print('{} VLAN ID: {}'.format(stream1.name, headers1.vlan[0].vid))
    print('{} IP DST: {}'.format(stream1.name, headers1.upper_layer.dst_s))

    headers1.vlan.clear()
    headers1.vlan.append(Dot1Q(vid=118, type=0x88A8))
    headers1.vlan.append(Dot1Q(vid=119, prio=7))
    stream1.set_packet_headers(headers1)

    stream1.add_modifier(position=14, min_val=0, max_val=7, mask='0xE0000000')
    stream1.add_modifier(position=18, min_val=119, max_val=218, mask='0x00FF0000')

    headers1_new = stream1.get_packet_headers()
    assert len(headers1_new.vlan) == 2


def run_all():
    connect()
    configuration()
    disconnect()


if __name__ == '__main__':
    run_all()
