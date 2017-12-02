"""
Base class for all Xena package tests.

@author yoram@ignissoft.com
"""

from os import path
import time

from trafficgenerator.test.test_tgn import TgnTest
from xenamanager.xena_app import init_xena


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
                for p_name, _ in module.ports.items():
                    print p_name
        print '+++'

    def test_load_config(self):
        self._load_config(path.join(path.dirname(__file__), 'configs', 'test_config.xpc'),
                          path.join(path.dirname(__file__), 'configs', 'test_config.xpc'))
        aaa = self.ports[self.port1].streams[0].get_attributes('ps_config')
        print aaa

    def test_online(self):
        self.ports = self.xm.session.reserve_ports([self.port1, self.port2], True)
        self.ports[self.port1].wait_for_up(16)
        self.ports[self.port2].wait_for_up(16)

    def test_traffic(self):
        self._load_config(path.join(path.dirname(__file__), 'configs', 'test_config.xpc'),
                          path.join(path.dirname(__file__), 'configs', 'test_config.xpc'))
        self.ports[self.port1].clear_stats()
        self.xm.session.start_traffic()
        time.sleep(4)
        self.xm.session.stop_traffic()
        print self.ports[self.port1].read_all_port_stats()

    def _load_config(self, cfg0, cfg1):
        self.ports = self.xm.session.reserve_ports([self.port1, self.port2], True)
        self.ports[self.port1].load_config(cfg0)
        self.ports[self.port2].load_config(cfg1)
