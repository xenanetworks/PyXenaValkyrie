
import logging
from pathlib import Path

import pytest
from _pytest.config.argparsing import Parser

from trafficgenerator.tgn_utils import ApiType
from trafficgenerator.tgn_conftest import (tgn_pytest_addoption, pytest_generate_tests, logger, api, server,
                                           server_properties)
from xenavalkyrie.xena_app import init_xena, XenaApp


def pytest_addoption(parser: Parser) -> None:
    """ Add options to allow the user to determine which APIs and servers to test. """
    tgn_pytest_addoption(parser, Path(__file__).parent.joinpath('test_config.py').as_posix())


@pytest.fixture(scope='session')
def xm(logger: logging.Logger, api: ApiType, server_properties: dict, locations: list) -> XenaApp:
    """ Yields server name in confing dict - generate tests will generate servers based on the server option. """
    server_ip, server_port = server_properties['server'].split(':')
    xm = init_xena(api, logger, 'pyxenavalkyrie', server_ip, int(server_port))
    chassis_list = [l.split('/')[0] for l in locations]
    for chassis in chassis_list:
        xm.session.add_chassis(chassis)
    yield xm
    xm.session.disconnect()


@pytest.fixture(scope='session')
def locations(server_properties: dict) -> list:
    """ Yields ports locations. """
    return server_properties['locations']
