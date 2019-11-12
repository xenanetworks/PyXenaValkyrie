"""
Base class for all Xena package tests.

@author yoram@ignissoft.com
"""

from os import path

from trafficgenerator.test.test_tgn import TestTgnBase
from xenavalkyrie.xena_app import init_xena
from xenavalkyrie.xena_stream import XenaStream


class TestXenaBase(TestTgnBase):

    TestTgnBase.config_file = path.join(path.dirname(__file__), 'XenaValkyrie.ini')

    def setup(self):
        super(TestXenaBase, self).setup()

        self.xm = init_xena(self.api, self.logger, self.config.get('Xena', 'owner'), self.server_ip, self.server_port)
        self.temp_dir = self.config.get('General', 'temp_dir')
        self.xm.session.add_chassis(self.chassis)
        if self.chassis2:
            self.xm.session.add_chassis(self.chassis2)
        XenaStream.next_tpld_id = 0

    def teardown(self):
        self.xm.session.disconnect()

    def test_hello_world(self):
        pass
