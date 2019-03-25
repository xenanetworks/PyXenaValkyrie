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
from xenavalkyrie.xena_port import XenaPort
from xenavalkyrie.xena_statistics_view import XenaPortsStats, XenaStreamsStats

api = ApiType.socket
ip = '176.22.65.117'
port0 = '0/0'
port1 = '0/1'
owner = 'worker'

#: :type xm: xenavalkyrie.xena_app.XenaApp
xm = None
chassis = None


def connect():
    """ Create Xena manager object and connect to chassis. """

    global xm
    global chassis

    # Xena manager requires standard logger. To log all low level CLI commands set DEBUG level.
    logger = logging.getLogger('log')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))

    # Create XenaApp object and connect to chassis.
    xm = init_xena(api, logger, owner, ip)
    chassis = xm.session.add_chassis(ip)


def disconnect():
    """ Disconnect from chassis. """

    xm.session.disconnect()


def measure():

    global ports

    # Pet ports
    XenaPort(parent=chassis, index=port0)
    XenaPort(parent=chassis, index=port1)

    port_stats = XenaPortsStats(xm.session)
    streams_stats = XenaStreamsStats(xm.session)

    # Loop for 10 seconds or any condition you want
    for _ in range(10):

        # Get statistics.
        port_stats.read_stats()
        streams_stats.read_stats()
        print(port_stats.statistics.dumps())
        print(streams_stats.statistics.dumps())

        time.sleep(1)


def run_all():
    connect()
    measure()
    disconnect()


if __name__ == '__main__':
    run_all()
