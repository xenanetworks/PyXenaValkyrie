#!/usr/bin/env python
# encoding: utf-8
""""
@author: yoram@ignissoft.com
"""

import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter

logger = None

version = 0.1


def xena_line_test(args=None):
    """ Xena line test script. """

    program_version = "v%s" % version
    program_version_message = '%%(prog)s %s' % (program_version)
    description = '''Run xena line test.'''

    # Setup argument parser
    parser = ArgumentParser(description=description,
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('-V', '--version', action='version', version=program_version_message)

    subparsers = parser.add_subparsers(help='type "xena_line_test [subcommand] -h" for help.')

    # save sub-parser
    save_convert = subparsers.add_parser('save', formatter_class=RawDescriptionHelpFormatter)
    save_convert.set_defaults(func=save_config)
    save_convert.add_argument('-o', '--output', required=True, metavar='file',
                              help='Configuration output file.')

    # load sub-parser
    load_analyze = subparsers.add_parser('load', formatter_class=RawDescriptionHelpFormatter)
    load_analyze.set_defaults(func=load_config)
    load_analyze.add_argument('-i', '--input', required=True, metavar='file',
                              help='Configuration input file.')

    # run sub-parser
    run_analyze = subparsers.add_parser('run', formatter_class=RawDescriptionHelpFormatter)
    run_analyze.set_defaults(func=run_test)
    run_analyze.add_argument('-p', '--ports', required=False, nargs='+', metavar='port',
                             help='Ports to start traffic on')
    run_analyze.add_argument('-t', '--time', required=True, type=int, metavar='int',
                             help='Run duration in seconds')
    run_analyze.add_argument('-r', '--results', required=True, metavar='file',
                             help='Results output file')

    # Process arguments
    parsed_args = parser.parse_args(args)

    parsed_args.func(parsed_args)


def save_config(parsed_args):
    pass


def load_config(parsed_args):
    pass


def run_test(parsed_args):
    pass


if __name__ == "__main__":
    sys.exit(xena_line_test((sys.argv[1:])))
