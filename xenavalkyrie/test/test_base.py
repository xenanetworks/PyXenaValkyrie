"""
Base class for all Xena package tests.

@author yoram@ignissoft.com
"""

from os import path

from trafficgenerator.test.test_tgn import TgnTest
from xenavalkyrie.xena_app import init_xena
from xenavalkyrie.xena_stream import XenaStream


class XenaTestBase(TgnTest):

    TgnTest.config_file = path.join(path.dirname(__file__), 'XenaValkyrie.ini')

    def setUp(self):
        super(XenaTestBase, self).setUp()
        self.xm = init_xena(self.api, self.logger, self.config.get('Xena', 'owner'),
                            self.config.get('Server', 'ip'), self.config.get('Server', 'port'))
        self.temp_dir = self.config.get('General', 'temp_dir')
        self.xm.session.add_chassis(self.config.get('Xena', 'chassis'))
        if self.xm.session.add_chassis(self.config.get('Xena', 'chassis2')):
            self.xm.session.add_chassis(self.config.get('Xena', 'chassis2'))
        self.port1 = '{}/{}'.format(self.config.get('Xena', 'chassis'), self.config.get('Xena', 'port1'))
        self.port2 = '{}/{}'.format(self.config.get('Xena', 'chassis'), self.config.get('Xena', 'port2'))
        self.port3 = self.config.get('Xena', 'port3')
        XenaStream.next_tpld_id = 0

    def tearDown(self):
        self.xm.session.disconnect()

    def test_hello_world(self):
        pass
