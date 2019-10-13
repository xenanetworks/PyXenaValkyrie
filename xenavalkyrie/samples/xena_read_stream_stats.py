"""
Stand alone samples demonstrating Xena package functionality.

Setup:
Two Xena ports connected back to back.

@author yoram@ignissoft.com
"""

from os import path
import sys
import logging
import json
import binascii
import time

from pypacker.layer12.ethernet import Ethernet, Dot1Q
from pypacker.layer3.ip6 import IP6
from pypacker.layer4.tcp import TCP

from trafficgenerator.tgn_utils import ApiType
from xenavalkyrie.xena_app import init_xena
from xenavalkyrie.xena_statistics_view import XenaPortsStats, XenaStreamsStats, XenaTpldsStats
from xenavalkyrie.xena_port import XenaCaptureBufferType
from xenavalkyrie.xena_tshark import Tshark, TsharkAnalyzer

wireshark_path = '/usr/bin'

api = ApiType.socket
chassis = '176.22.65.117'
port1 = chassis + '/' + '0/0'
port0 = chassis + '/' + '0/1'
owner = 'yoram-s'
config0 = path.join(path.dirname(__file__), 'Port0_3stream.xpc')
config1 = path.join(path.dirname(__file__), 'Port1_4stream.xpc')
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
    ports[port0].load_config(config0)
    ports[port1].load_config(config1)


def traffic():

    xm.session.clear_stats()
    xm.session.start_traffic(blocking=False)
    time.sleep(8)
    xm.session.stop_traffic()

    streams_stats = XenaStreamsStats(xm.session)
    streams_stats.read_stats()
    print(streams_stats.statistics.dumps())


def run_all():
    connect()
    configuration()
    traffic()
    disconnect()


if __name__ == '__main__':
    run_all()
