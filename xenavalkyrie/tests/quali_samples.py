"""
Sample showing how Xena can integrate with CloudShell and Jenkins.

Setup:
Two Xena ports connected back to back.

@author yoram@ignissoft.com
"""

from os import path, environ
import sys
import logging
import json

from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.traffic.tg_helper import get_reservation_resources, get_address
from shellfoundry.releasetools.test_helper import create_command_context, end_reservation

from xenavalkyrie.xena_app import init_xena
from xenavalkyrie.xena_statistics_view import XenaPortsStats, XenaStreamsStats, XenaTpldsStats

owner = 'yoram-s'
config1 = path.join(path.dirname(__file__), 'configs', 'test_config.xpc')
config2 = path.join(path.dirname(__file__), 'configs', 'test_config.xpc')

xm = None
chassis = None
port1 = None
port2 = None
session = None
sandbox_id = None


def get_reservation_resources(session, reservation_id, model_name):

    reservation_resources = []
    reservation = session.GetReservationDetails(reservation_id).ReservationDescription
    for resource in reservation.Resources:
        if resource.ResourceModelName == model_name:
            reservation_resources.append(resource)
    return reservation_resources


def connect():
    """ Create Xena manager object and connect to chassis. """

    global xm
    global chassis
    global port1
    global port2
    global session
    global sandbox_id

    session = CloudShellAPISession('localhost', 'admin', 'admin', 'Global')
    if 'SANDBOX_ID' in environ:
        sandbox_id = environ['SANDBOX_ID']
    else:
        context = create_command_context(session, ['xena 2g/Module6/Port0', 'xena 2g/Module6/Port1'],
                                         'Xena Controller', {})
        sandbox_id = context.reservation.reservation_id

    reserved_port1, reserved_port2 = get_reservation_resources(session, sandbox_id,
                                                               'Xena Chassis Shell 2G.GenericTrafficGeneratorPort')
    port1 = get_address(reserved_port1)
    port2 = get_address(reserved_port2)
    chassis = port1.split('/')[0]

    logger = logging.getLogger('log')
    logger.setLevel('INFO')
    logger.addHandler(logging.StreamHandler(sys.stdout))
    xm = init_xena(logger, owner)

    xm.session.add_chassis(chassis)


def disconnect():
    """ Disconnect from chassis. """

    xm.logoff()
    if 'SANDBOX_ID' not in environ:
        end_reservation(session, sandbox_id)


def load_config():
    """ Reserve ports, load configuration and wait for ports up. """

    ports = xm.session.reserve_ports([port1, port2], True)
    ports[port1].load_config(config1)
    ports[port2].load_config(config2)
    ports[port1].wait_for_up(16)
    ports[port2].wait_for_up(16)


def traffic():
    """ Load configuration and, run traffic and print statistics. """

    ports = xm.session.reserve_ports([port1, port2], True)
    ports[port1].load_config(config1)
    ports[port2].load_config(config2)
    ports[port1].wait_for_up(16)
    ports[port2].wait_for_up(16)

    xm.session.clear_stats()
    xm.session.start_traffic(blocking=True)
    ports_stats = XenaPortsStats(xm.session)
    ports_stats.read_stats()
    print(json.dumps(ports_stats.statistics, indent=1))
    streams_stats = XenaStreamsStats(xm.session)
    streams_stats.read_stats()
    print(json.dumps(streams_stats.statistics, indent=1))
    tplds_stats = XenaTpldsStats(xm.session)
    tplds_stats.read_stats()
    print(json.dumps(tplds_stats.statistics, indent=1))


def run_all():
    connect()
    load_config()
    traffic()
    disconnect()


if __name__ == '__main__':
    run_all()
