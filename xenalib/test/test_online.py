"""
Base class for all Xena package tests.

@author yoram@ignissoft.com
"""

from os import path

from trafficgenerator.test.test_tgn import TgnTest
from xenalib.xena_app import init_xena


class XenaTestBase(TgnTest):

    TgnTest.config_file = path.join(path.dirname(__file__), 'XenaManager.ini')

    def setUp(self):
        super(XenaTestBase, self).setUp()
        self.xm = init_xena(self.logger, self.config.get('Xena', 'chassis'))
        self.xm.connect('yoram-s')

    def tearDown(self):
        self.xm.session.release_ports()

    def test_inventory(self):
        self.xm.chassis.inventory()

    def test_load_config(self):
        self.ports = self.xm.session.reserve_ports([self.config.get('Xena', 'port1'),
                                                    self.config.get('Xena', 'port2')], True)
        self.ports[0].load_config(path.join(path.dirname(__file__), 'configs', 'XB live demo-6-0.xpc'))
