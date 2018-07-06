"""
Test all kinds of errors.

@author yoram@ignissoft.com
"""

from os import path

from trafficgenerator.tgn_utils import ApiType
from trafficgenerator.test.test_tgn import TgnTest
from xenamanager.xena_app import init_xena
from xenamanager.api.XenaSocket import XenaCommandException
from xenamanager.api.xena_rest import XenaRestWrapper


class XenaTestErrors(TgnTest):

    TgnTest.config_file = path.join(path.dirname(__file__), 'XenaManager.ini')

    def setUp(self):
        super(XenaTestErrors, self).setUp()
        self.xm = init_xena(ApiType[self.config.get('Xena', 'api')], self.logger, self.config.get('Xena', 'owner'),
                            self.config.get('Server', 'ip'), self.config.get('Server', 'port'))

    def tearDown(self):
        self.xm.session.disconnect()

    def test_errors(self):

        if type(self.xm.session.api) is XenaRestWrapper:
            self.skipTest('Skip test - REST API')

        self.assertRaises(IOError, self.xm.session.add_chassis, 'invalid IP')
        assert(len(self.xm.session.chassis_list) == 0)

        self.xm.session.add_chassis(self.config.get('Xena', 'chassis'))
        self.port1 = '{}/{}'.format(self.config.get('Xena', 'chassis'), self.config.get('Xena', 'port1'))

        xm = init_xena(ApiType[self.config.get('Xena', 'api')], self.logger, self.config.get('Xena', 'owner'),
                       self.config.get('Server', 'ip'), self.config.get('Server', 'port'))
        xm.session.add_chassis(self.config.get('Xena', 'chassis'))

        #: :type port: xenamanager.xena_port.XenaPort
        port = self.xm.session.reserve_ports([self.port1], True)[self.port1]

        #: :type api: xenamanager.api.XenaSocket.XenaSocket

        self.assertRaises(XenaCommandException, port.get_attribute, 'ps_packetlimit')

        # test read only

        self.assertRaises(NotImplementedError,
                          self.xm.session.chassis_list[self.config.get('Xena', 'chassis')].get_session_id)
