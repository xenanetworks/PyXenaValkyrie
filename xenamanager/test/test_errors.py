"""
Test all kinds of errors.

@author yoram@ignissoft.com
"""

from os import path

from trafficgenerator.test.test_tgn import TgnTest
from xenamanager.xena_app import init_xena
from xenamanager.api.XenaSocket import XenaCommandException


class XenaTestBase(TgnTest):

    TgnTest.config_file = path.join(path.dirname(__file__), 'XenaManager.ini')

    def setUp(self):
        super(XenaTestBase, self).setUp()
        self.xm = init_xena(self.logger, self.config.get('Xena', 'owner'))

    def tearDown(self):
        self.xm.logoff()

    def test_errors(self):

        self.assertRaises(IOError, self.xm.session.add_chassis, 'invalid IP')

        self.xm.session.add_chassis(self.config.get('Xena', 'chassis'))
        self.port1 = self.config.get('Xena', 'port1')

        #: :type port: xenamanager.xena_port.XenaPort
        port = self.xm.session.reserve_ports([self.port1], True)[self.port1]

        #: :type api: xenamanager.api.XenaSocket.XenaSocket
        api = port.api

        api.connect()

        self.assertRaises(XenaCommandException, port.get_attribute, 'ps_packetlimit')
        self.assertRaises(XenaCommandException, port.get_attributes, 'ps_packetlimit')

        self.assertRaises(XenaCommandException, port.api.sendQuery, 'p_comment 4/6 ?')

        api.connect()

        # test read only
