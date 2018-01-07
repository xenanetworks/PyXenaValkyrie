"""
Stand alone samples demonstrating Xena package functionality.

Setup:
Two Xena ports connected back to back.

@author yoram@ignissoft.com
"""

import sys
import logging
import json

from xenamanager.xena_app import init_xena
from xenamanager.xena_statistics_view import XenaPortsStats, XenaStreamsStats, XenaTpldsStats

chassis = '176.22.65.114'
port1 = chassis + '/' + '8/0'
port2 = chassis + '/' + '8/1'
owner = 'yoram-s'
config1 = 'E:/workspace/python/PyXenaManager/xenamanager/test/configs/test_config.xpc'
config2 = 'E:/workspace/python/PyXenaManager/xenamanager/test/configs/test_config.xpc'

xm = None


def connect():
    """ Create Xena manager object and connect to chassis. """

    global xm

    logger = logging.getLogger('log')
    logger.setLevel('DEBUG')
    logger.addHandler(logging.StreamHandler(sys.stdout))
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
    print json.dumps(streams_stats.statistics, indent=1)
    tplds_stats = XenaTpldsStats(xm.session)
    tplds_stats.read_stats()
    print json.dumps(tplds_stats.statistics, indent=1)


def run_all():
    connect()
    load_config()
    traffic()
    disconnect()


if __name__ == '__main__':
    run_all()
