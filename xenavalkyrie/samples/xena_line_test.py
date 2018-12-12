#!/usr/bin/env python
# encoding: utf-8
""""
@author: yoram@ignissoft.com
"""

import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import logging
import time
import json

from trafficgenerator.tgn_utils import ApiType
from xenavalkyrie.xena_app import init_xena
from xenavalkyrie.xena_port import XenaPort
from xenavalkyrie.xena_stream import XenaStreamState
from xenavalkyrie.xena_statistics_view import XenaPortsStats


version = 0.2


def xena_line_test(args=None):
    """ Xena line test script. """

    program_version = "v%s" % version
    program_version_message = '%%(prog)s %s' % (program_version)
    description = '''Run xena line test.'''

    # Setup argument parser
    parser = ArgumentParser(description=description,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-V', '--version', action='version', version=program_version_message)

    parser.add_argument('-l', '--log', required=False, default='xena_line_test_log.txt', metavar='file',
                        help='Log file')
    parser.add_argument('-c', '--chassis', required=True, metavar='chassis',
                        help='Xena line chassis')

    subparsers = parser.add_subparsers(help='type "xena_line_test [subcommand] -h" for help.')

    # save sub-parser
    save_convert = subparsers.add_parser('save', formatter_class=ArgumentDefaultsHelpFormatter)
    save_convert.set_defaults(func=save_config)
    save_convert.add_argument('-p', '--ports', required=False, nargs='+', metavar='port',
                              help='Ports to start traffic on')
    save_convert.add_argument('-o', '--output', required=True, metavar='file',
                              help='Configuration output file.')

    # load sub-parser
    load_analyze = subparsers.add_parser('load', formatter_class=ArgumentDefaultsHelpFormatter)
    load_analyze.set_defaults(func=load_config)
    load_analyze.add_argument('-i', '--input', required=True, metavar='file',
                              help='Configuration input file.')

    # run sub-parser
    run_analyze = subparsers.add_parser('run', formatter_class=ArgumentDefaultsHelpFormatter)
    run_analyze.set_defaults(func=run_test)
    run_analyze.add_argument('-p', '--ports', required=True, nargs='+', metavar='port',
                             help='Ports to start traffic on')
    run_analyze.add_argument('-t', '--time', required=True, type=int, metavar='int',
                             help='Run duration in seconds')
    run_analyze.add_argument('-r', '--results', required=True, metavar='file',
                             help='Results output file')

    # Process arguments
    parsed_args = parser.parse_args(args)

    parsed_args.func(parsed_args)


def save_config(parsed_args):
    chassis = connect(parsed_args.log, parsed_args.chassis)

    chassis.inventory(modules_inventory=True)
    ports_per_module = [m.ports.values() for m in chassis.modules.values()]
    inventory_ports = {p.index: p for m in ports_per_module for p in m}

    if not parsed_args.ports:
        ports = inventory_ports.keys()
    else:
        ports = parsed_args.ports

    with open(parsed_args.output, 'w+') as _:
        pass

    for port in ports:
        inventory_ports[port].save_config(parsed_args.output, 'a+')

    chassis.api.disconnect()


def load_config(parsed_args):
    chassis = connect(parsed_args.log, parsed_args.chassis)

    with open(parsed_args.input) as f:
        commands = f.read().splitlines()

    for command in commands:
        if command.startswith(';'):
            port = XenaPort(chassis, command.split(':')[1].strip())
            port.reserve(force=True)
        elif command.startswith('P_LPTXMODE'):
            pass
        else:
            if not command.startswith('P_LPTXMODE'):
                port.send_command(command)

    for port in chassis.ports.values():
        port.release()


def run_test(parsed_args):
    chassis = connect(parsed_args.log, parsed_args.chassis)

    for port in parsed_args.ports:
        XenaPort(chassis, port).reserve(force=True)

    for port in chassis.ports.values():
        port.clear_stats()
        for stream in port.streams.values():
            stream.set_state(XenaStreamState.enabled)

    chassis.start_traffic()
    time.sleep(parsed_args.time)
    chassis.stop_traffic()

    time.sleep(2)

    with open(parsed_args.results, 'w+') as f:
        ports_stats = XenaPortsStats(chassis.parent)
        ports_stats.read_stats()
        f.write(json.dumps(ports_stats.get_flat_stats(), indent=2))

    for port in chassis.ports.values():
        port.release()


def connect(log_file, chassis):

    # Xena manager requires standard logger. To log all low level CLI commands set DEBUG level.
    logger = logging.getLogger('log')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.addHandler(logging.FileHandler(log_file))

    # Create XenaApp object and connect to chassis.
    xm = init_xena(ApiType.socket, logger, 'xena_line_test', chassis)
    return xm.session.add_chassis(chassis)


if __name__ == "__main__":
    sys.exit(xena_line_test((sys.argv[1:])))
