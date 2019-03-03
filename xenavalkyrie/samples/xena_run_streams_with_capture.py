"""
Load multi stream configuration and run streams one by one, save results and first packet of each stream in a file.

Setup:
Two Xena ports connected back to back.

@author yoram@ignissoft.com
"""

import sys
import logging
import time

from trafficgenerator.tgn_utils import ApiType
from xenavalkyrie.xena_app import init_xena
from xenavalkyrie.xena_statistics_view import XenaPortsStats, XenaStreamsStats
from xenavalkyrie.xena_port import XenaCaptureBufferType

wireshark_path = '/usr/bin'

api = ApiType.socket
chassis = '192.168.1.197'
chassis = '176.22.65.117'
port0 = chassis + '/' + '0/0'
port1 = chassis + '/' + '0/1'
owner = 'yoram-s'
config0 = 'test_config_long_packets.xpc'
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


def traffic():

    global ports

    with open(cap_file, 'w+') as _:
        pass

    with open(results_file, 'w+') as _:
        pass

    # Reserve ports
    ports = xm.session.reserve_ports([port0, port1], True)
    ports[port0].wait_for_up(16)
    ports[port1].wait_for_up(16)

    # Load configuration on port-0.
    ports[port0].load_config(config0)

    # Disable all streams
    for stream in ports[port0].streams.values():
        stream.set_attributes(PS_ENABLE='OFF')

    for sid, stream in ports[port0].streams.items():

        # Enable current stream
        stream.set_attributes(PS_ENABLE='ON')

        # Run traffic with capture on all ports.

        # Run traffic on one port and capture on the other port.
        xm.session.clear_stats()
        ports[port1].start_capture()
        ports[port0].start_traffic(blocking=True)
        ports[port1].stop_capture()

        # Get port level statistics.
        streams_stats = XenaStreamsStats(xm.session)
        streams_stats.read_stats()
        print(streams_stats.statistics.dumps())

        with open(results_file, 'a+') as f:
            f.write('{} TX packets = {}\n'.format(stream.name,
                                                  streams_stats.statistics[stream.name]['tx']['packets']))
            f.write('{} RX packets = {}\n'.format(stream.name,
                                                  streams_stats.statistics[stream.name]['rx']['pr_tpldtraffic']['pac']))
            f.write('{} TX bytes = {}\n'.format(stream.name,
                                                streams_stats.statistics[stream.name]['tx']['bytes']))
            f.write('{} RX bytes = {}\n'.format(stream.name,
                                                streams_stats.statistics[stream.name]['rx']['pr_tpldtraffic']['byt']))

        # Get first captured packet in raw format.
        packet = ports[port1].capture.get_packets(to_index=1, cap_type=XenaCaptureBufferType.text)[0]
        with open(cap_file, 'a+') as f:
            f.write('{} first packet = {}\n\n'.format(stream.name, packet))

        # Disable current stream
        stream.set_attributes(PS_ENABLE='OFF')


def run_all():
    connect()
    traffic()
    disconnect()


if __name__ == '__main__':
    run_all()
