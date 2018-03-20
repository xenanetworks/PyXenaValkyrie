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

from xenamanager.xena_app import init_xena
from xenamanager.xena_statistics_view import XenaPortsStats, XenaStreamsStats, XenaTpldsStats

chassis = '176.22.65.114'
port1 = chassis + '/' + '6/4'
port2 = chassis + '/' + '6/5'
owner = 'yoram-s'
config1 = path.join(path.dirname(__file__), 'configs', 'test_config_1.xpc')
config2 = path.join(path.dirname(__file__), 'configs', 'test_config_2.xpc')

#: :type xm: xenamanager.xena_app.XenaManager
xm = None


def connect():
    """ Create Xena manager object and connect to chassis. """

    global xm

    # Xena manager requires standard logger. To log all low level CLI commands set DEBUG level.
    logger = logging.getLogger('log')
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler(sys.stdout))

    # Create XenaManager object and connect to chassis.
    xm = init_xena(logger, owner)
    xm.session.add_chassis(chassis)


def disconnect():
    """ Disconnect from chassis. """

    xm.logoff()


def inventory():
    """ Get inventory of all chassis. """

    xm.session.inventory()
    print('+++')
    for c_name, chassis in xm.session.chassis_list.items():
        print('chassis ' + c_name)
        for m_name, module in chassis.modules.items():
            print('\tmodule ' + str(m_name))
            for p_name, _ in module.ports.items():
                print('\t\tport ' + str(p_name))
    print('+++')


def load_config():
    """ Reserve ports.
        Wait for ports up.
        Load configuration on one port.
        Build configuration on the second port.
    """

    ports = xm.session.reserve_ports([port1, port2], True)
    ports[port1].wait_for_up(16)
    ports[port2].wait_for_up(16)
    ports[port1].load_config(config1)

    # Get port-1/stream-1 object.
    stream_obj = ports[port1].streams[0]

    # Get Multi-parameter query with get_attributes which returns all attributes values as dict.
    ps_config = stream_obj.get_attributes('ps_config')
    print('{} info:\n{}'.format(stream_obj.name, json.dumps(ps_config, indent=1)))

    # Add stream on port-2
    stream_obj = ports[port1].add_stream('new stream')

    # Set ps_packetlimit and ps_ratepps with set_attributes which sets list of attributes.
    stream_obj.set_attributes(ps_packetlimit=800, ps_ratepps=100)

    # Get single parameter query with get_attribute which returns the attribute value as str.
    ps_packetlimit = stream_obj.get_attribute('ps_packetlimit')
    ps_ratepps = stream_obj.get_attribute('ps_ratepps')
    print('{} info:\nps_packetlimit: {}\nps_ratepps: {}'.format(stream_obj.name, ps_packetlimit, ps_ratepps))


def traffic():
    """ Load configuration, run traffic and print statistics. """

    xm.session.clear_stats()
    xm.session.start_traffic(blocking=True)

    ports_stats = XenaPortsStats(xm.session)
    ports_stats.read_stats()
    print(ports_stats.statistics.dumps())

    streams_stats = XenaStreamsStats(xm.session)
    streams_stats.read_stats()
    print(streams_stats.statistics.dumps())

    tplds_stats = XenaTpldsStats(xm.session)
    tplds_stats.read_stats()
    print(tplds_stats.statistics.dumps())


def run_all():
    connect()
    inventory()
    load_config()
    traffic()
    disconnect()


if __name__ == '__main__':
    run_all()
