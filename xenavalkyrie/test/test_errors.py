"""
Test all kinds of errors.

@author yoram@ignissoft.com
"""

from os import path

from trafficgenerator.test.test_tgn import TgnTest
from xenavalkyrie.xena_app import init_xena
from xenavalkyrie.xena_object import XenaAttributeError


class XenaTestErrors(TgnTest):

    TgnTest.config_file = path.join(path.dirname(__file__), 'XenaValkyrie.ini')

    def setUp(self):
        super(XenaTestErrors, self).setUp()
        self.xm = init_xena(self.api, self.logger, self.config.get('Xena', 'owner'),
                            self.config.get('Server', 'ip'), self.config.get('Server', 'port'))
        self.port1 = '{}/{}'.format(self.config.get('Xena', 'chassis'), self.config.get('Xena', 'port1'))

    def tearDown(self):
        self.xm.session.disconnect()

    def test_errors(self):

        # Test invalid chassis IP and port number.

        with self.assertRaises(Exception) as cm:
            self.xm.session.add_chassis('InvalidIp')
        assert('IOError' in repr(cm.exception) or 'OSError' in repr(cm.exception))
        assert(len(self.xm.session.chassis_list) == 0)

        with self.assertRaises(Exception) as cm:
            self.xm.session.add_chassis(self.config.get('Xena', 'chassis'), -17)
        assert('IOError' in repr(cm.exception) or 'OSError' in repr(cm.exception))
        assert(len(self.xm.session.chassis_list) == 0)

        # Reserve port to continue testing...

        self.xm.session.add_chassis(self.config.get('Xena', 'chassis'))
        port = self.xm.session.reserve_ports([self.port1], True)[self.port1]

        # Test attributes errors.

        self.assertRaises(XenaAttributeError, port.get_attribute, 'InvalidAttribute')
        self.assertRaises(XenaAttributeError, port.set_attributes, p_reservation=17)
        self.assertRaises(XenaAttributeError, port.set_attributes, p_reservedby=17)
