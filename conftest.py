
def pytest_addoption(parser):
    parser.addoption(
        "--api", action="store", default="socket", help="api option: socket or rest"
    )
