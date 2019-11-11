
import pytest


def pytest_addoption(parser):
    parser.addoption("--api", action="store", default="socket", help="api option: socket or rest")
    parser.addoption("--server", action="store", default="localhost:57913",
                     help="REST server, options: 'test' or server IP, default: server == chassis")
    parser.addoption("--chassis", action="store", default="176.22.65.117", help="chassis IP address")
    parser.addoption("--port1", action="store", default="0/0", help="module1/port1")
    parser.addoption("--port2", action="store", default="0/1", help="module2/port2")
    parser.addoption("--port3", action="store", default="", help="ip/module3/port3 must support extended modifiers")
    parser.addoption('--port', action='append', default=['0/0', '0/1'], help='module/port')


@pytest.fixture(scope='session')
def api(pytestconfig):
    yield pytestconfig.getoption('api')
