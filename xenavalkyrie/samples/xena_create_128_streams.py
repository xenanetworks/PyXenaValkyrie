"""
Stand alone samples demonstrating Xena package functionality.

Setup:
Two Xena ports connected back to back.

@author yoram@ignissoft.com
"""

import sys
import logging

from trafficgenerator.tgn_utils import ApiType
from xenavalkyrie.xena_app import init_xena

api = ApiType.rest
server = '176.22.65.117'
chassis = '192.168.1.197'
port0 = chassis + '/' + '0/0'
port1 = chassis + '/' + '0/1'
owner = 'yoram-s'
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
    xm = init_xena(api, logger, owner, server, port=57912)
    xm.session.add_chassis(chassis)


def disconnect():
    """ Disconnect from chassis. """

    xm.session.disconnect()


def configuration():

    global ports

    ports = xm.session.reserve_ports([port0, port1], True)
    ports[port0].wait_for_up(16)
    ports[port1].wait_for_up(16)

    # Add 128 stream on port-1
    for s in range(0, 128):
        ports[port0].add_stream('port 0 stream {}'.format(s))
        ports[port1].add_stream('port 1 stream {}'.format(s))


def run_all():
    connect()
    configuration()
    disconnect()


if __name__ == '__main__':
    run_all()
