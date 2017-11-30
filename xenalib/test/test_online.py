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
        self.xm = init_xena(self.logger)
        self.xm.add_chassis(self.config.get('Xena', 'chassis'), 'yoram-s')
        self.port1 = self.config.get('Xena', 'port1')
        self.port2 = self.config.get('Xena', 'port2')

    def tearDown(self):
        self.xm.disconnect()

    def test_inventory(self):
        self.xm.session.inventory()
        print '+++'
        for c_name, chassis in self.xm.session.chassis_list.items():
            print c_name
            for m_name, module in chassis.modules.items():
                print m_name
                for p_name, port in module.ports.items():
                    print p_name
        print '+++'

    def test_load_config(self):
        self.ports = self.xm.session.reserve_ports([self.port1, self.port2], True)
        self._load_config(path.join(path.dirname(__file__), 'configs', 'XB live demo-6-0.xpc'),
                          path.join(path.dirname(__file__), 'configs', 'XB live demo-6-0.xpc'))

    def test_port_online(self):
        pass

    def _load_config(self, cfg0, cfg1):
        self.ports[self.port1].load_config(cfg0)
        self.ports[self.port2].load_config(cfg1)
