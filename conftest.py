
def pytest_addoption(parser):
    parser.addoption("--api", action="store", default="rest", help="api option: socket or rest")
    parser.addoption("--server", action="store", default="", help="server option: REST server")
    parser.addoption("--chassis", action="store", default="192.168.1.197", help="chassis IP address")
    parser.addoption("--port1", action="store", default="0/0", help="module1/port1")
    parser.addoption("--port2", action="store", default="0/1", help="module2/port2")
