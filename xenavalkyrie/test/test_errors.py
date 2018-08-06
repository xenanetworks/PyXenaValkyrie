"""
Test all kinds of errors.

@author yoram@ignissoft.com
"""

from xenavalkyrie.xena_app import init_xena
from xenavalkyrie.xena_object import XenaAttributeError
from xenavalkyrie.test.test_base import XenaTestBase


class XenaTestErrors(XenaTestBase):

    def setUp(self):
        super(XenaTestBase, self).setUp()

        self._get_config()

        self.xm = init_xena(self.api, self.logger, self.config.get('Xena', 'owner'),
                            self.server_ip, self.server_port)

    def tearDown(self):
        self.xm.session.disconnect()

    def test_errors(self):

        # Test invalid chassis IP and port number.

        with self.assertRaises(Exception) as cm:
            self.xm.session.add_chassis('InvalidIp')
        assert('IOError' in repr(cm.exception) or 'OSError' in repr(cm.exception))
        assert(len(self.xm.session.chassis_list) == 0)

        with self.assertRaises(Exception) as cm:
            self.xm.session.add_chassis(self.chassis, -17)
        assert('IOError' in repr(cm.exception) or 'OSError' in repr(cm.exception))
        assert(len(self.xm.session.chassis_list) == 0)

        # Reserve port to continue testing...

        self.xm.session.add_chassis(self.chassis)
        port = self.xm.session.reserve_ports([self.port1], True)[self.port1]

        # Test attributes errors.

        self.assertRaises(XenaAttributeError, port.get_attribute, 'InvalidAttribute')
        self.assertRaises(XenaAttributeError, port.set_attributes, p_reservation=17)
        self.assertRaises(XenaAttributeError, port.set_attributes, p_reservedby=17)
