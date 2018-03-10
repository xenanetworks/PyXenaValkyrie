"""
Base class for all Xena package tests.

@author yoram@ignissoft.com
"""

from os import path

from trafficgenerator.test.test_tgn import TgnTest
from xenamanager.xena_app import init_xena


class XenaTestBase(TgnTest):

    TgnTest.config_file = path.join(path.dirname(__file__), 'XenaManager.ini')

    def setUp(self):
        super(XenaTestBase, self).setUp()
        self.xm = init_xena(self.logger, self.config.get('Xena', 'owner'))
        self.xm.session.add_chassis(self.config.get('Xena', 'chassis'))
        self.port1 = self.config.get('Xena', 'port1')
        self.port2 = self.config.get('Xena', 'port2')

    def tearDown(self):
        self.xm.logoff()

    def test_hello_world(self):
        pass
