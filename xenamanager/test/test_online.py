"""
Base class for all Xena package tests.

@author yoram@ignissoft.com
"""

from os import path
import time
import json

from trafficgenerator.test.test_tgn import TgnTest
from xenamanager.xena_app import init_xena
from xenamanager.xena_statistics_view import XenaPortsStats, XenaStreamsStats, XenaTpldsStats


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

    def test_inventory(self):
        self.xm.session.inventory()
        print('+++')
        for c_name, chassis in self.xm.session.chassis_list.items():
            print(c_name)
            for m_name, module in chassis.modules.items():
                print(m_name)
                for p_name, _ in module.ports.items():
                    print(p_name)
        print('+++')

    def test_load_config(self):
        self._load_config(path.join(path.dirname(__file__), 'configs', 'test_config.xpc'),
                          path.join(path.dirname(__file__), 'configs', 'test_config.xpc'))

    def test_online(self):
        self.ports = self.xm.session.reserve_ports([self.port1, self.port2], True)
        self.ports[self.port1].wait_for_up(16)
        self.ports[self.port2].wait_for_up(16)

    def test_traffic(self):
        self._load_config(path.join(path.dirname(__file__), 'configs', 'test_config.xpc'),
                          path.join(path.dirname(__file__), 'configs', 'test_config.xpc'))
        self.xm.session.start_traffic()
        time.sleep(2)
        port1_stats = self.ports[self.port1].read_port_stats()
        port2_stats = self.ports[self.port2].read_port_stats()
        assert(abs(port1_stats['pt_total']['packets'] - port2_stats['pr_total']['packets']) < 3000)
        assert(abs(1000 - self.ports[self.port1].streams[0].read_stats()['pps']) < 10)
        assert(abs(1000 - self.ports[self.port1].tplds[0].read_stats()['pr_tpldtraffic']['pps']) < 10)
        self.xm.session.stop_traffic()
        self.xm.session.clear_stats()
        self.xm.session.start_traffic(blocking=True)
        ports_stats = XenaPortsStats(self.xm.session)
        ports_stats.read_stats()
        print json.dumps(ports_stats.statistics, indent=1)
        print json.dumps(ports_stats.get_flat_stats(), indent=1)
        streams_stats = XenaStreamsStats(self.xm.session)
        streams_stats.read_stats()
        print json.dumps(streams_stats.statistics, indent=1)
        print json.dumps(streams_stats.get_flat_stats(), indent=1)
        tplds_stats = XenaTpldsStats(self.xm.session)
        tplds_stats.read_stats()
        print json.dumps(tplds_stats.statistics, indent=1)
        print json.dumps(tplds_stats.get_flat_stats(), indent=1)

    def test_traffic(self):
        self._load_config(path.join(path.dirname(__file__), 'configs', 'test_config.xpc'),
                          path.join(path.dirname(__file__), 'configs', 'test_config.xpc'))
        self.ports[self.port1].start_capture()
        self.ports[self.port1].start_traffic(blocking=True)
        self.ports[self.port1].stop_capture()
        packets = self.ports[self.port1].capture.get_packets(1, 2)
        print packets[0]
        print packets[1]

    def _load_config(self, cfg0, cfg1):
        self.ports = self.xm.session.reserve_ports([self.port1, self.port2], True)
        self.ports[self.port1].load_config(cfg0)
        self.ports[self.port2].load_config(cfg1)
