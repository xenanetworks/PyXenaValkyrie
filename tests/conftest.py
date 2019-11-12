
import pytest

from trafficgenerator.tgn_utils import ApiType


def pytest_addoption(parser):
    parser.addoption("--api", action="append", default=['socket'], help="api option: socket or rest")
    parser.addoption("--server", action="store", default="localhost:57912",
                     help="REST server, options: 'test' or server IP, default: server == chassis")
    parser.addoption("--chassis", action="store", default="176.22.65.117", help="chassis IP address")
    parser.addoption("--port1", action="store", default="0/0", help="module1/port1")
    parser.addoption("--port2", action="store", default="0/1", help="module2/port2")
    parser.addoption("--port3", action="store", default="", help="ip/module3/port3 must support extended modifiers")
    parser.addoption('--port', action='append', default=['0/0', '0/1'], help='module/port')


@pytest.fixture(scope='class', autouse=True)
def api(request):
    request.cls.api = ApiType[request.param]
    request.cls.server_ip = request.config.getoption('--server')
    request.cls.chassis = request.config.getoption('--chassis')
    request.cls.port1 = '{}/{}'.format(request.cls.chassis, request.config.getoption('--port1'))
    request.cls.port2 = '{}/{}'.format(request.cls.chassis, request.config.getoption('--port2'))
    request.cls.port3 = request.config.getoption('--port3')
    request.cls.chassis2 = request.cls.port3.split('/')[0] if request.cls.port3 else ''
    if request.cls.server_ip:
        request.cls.server_port = (int(request.cls.server_ip.split(':')[1]) if
                                   len(request.cls.server_ip.split(':')) == 2 else 57911)
        request.cls.server_ip = request.cls.server_ip.split(':')[0]
    else:
        request.cls.server_ip = request.cls.chassis
        request.cls.server_port = 57911


def pytest_generate_tests(metafunc):
    metafunc.parametrize('api', metafunc.config.getoption('api'), indirect=True)
