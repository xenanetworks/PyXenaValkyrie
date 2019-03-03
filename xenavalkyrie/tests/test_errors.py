"""
Test all kinds of errors.

@author yoram@ignissoft.com
"""

import pytest

from xenavalkyrie.xena_app import init_xena
from xenavalkyrie.xena_object import XenaAttributeError
from xenavalkyrie.tests.test_base import TestXenaBase
from trafficgenerator.tgn_utils import ApiType


class TestXenaErrors(TestXenaBase):

    def setup(self):
        super(TestXenaBase, self).setup()

        self._get_config()

        self.xm = init_xena(self.api, self.logger, self.config.get('Xena', 'owner'),
                            self.server_ip, self.server_port)

    def teardown(self):
        self.xm.session.disconnect()

    def test_errors(self):

        # Test invalid chassis IP and port number.

        with pytest.raises(Exception) as excinfo:
            self.xm.session.add_chassis('InvalidIp')
        assert('IOError' in repr(excinfo.value) or 'OSError' in repr(excinfo.value))
        assert(len(self.xm.session.chassis_list) == 0)

        if self.api == ApiType.socket:
            with pytest.raises(Exception) as excinfo:
                self.xm.session.add_chassis(self.chassis, -17)
            assert('IOError' in repr(excinfo.value) or 'OSError' in repr(excinfo.value))
            assert(len(self.xm.session.chassis_list) == 0)

        # Reserve port to continue testing...

        self.xm.session.add_chassis(self.chassis)
        port = self.xm.session.reserve_ports([self.port1], True)[self.port1]

        # Test attributes errors.

        with pytest.raises(XenaAttributeError) as _:
            port.get_attribute('InvalidAttribute')
        with pytest.raises(XenaAttributeError) as _:
            port.set_attributes(p_reservation=17)
        with pytest.raises(XenaAttributeError) as _:
            port.set_attributes(p_reservedby=17)
