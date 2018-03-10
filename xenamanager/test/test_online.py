"""
Tests that require online ports.

Most tests use loopback port as this is the simplest configuration.
Some tests require two back-to-back ports, like stream statistics tests.

@author yoram@ignissoft.com
"""

from os import path
import time
import json

from xenamanager.xena_statistics_view import XenaPortsStats, XenaStreamsStats, XenaTpldsStats
from xenamanager.test.test_base import XenaTestBase


class XenaTestOnline(XenaTestBase):

    def test_online(self):
        self.ports = self.xm.session.reserve_ports([self.port1, self.port2], True)
        self.ports[self.port1].wait_for_up(16)
        self.ports[self.port2].wait_for_up(16)

    def test_traffic(self):
        port = self.xm.session.reserve_ports([self.port1])[self.port1]
        port.load_config(path.join(path.dirname(__file__), 'configs', 'test_config_loopback.xpc'))

        self.xm.session.clear_stats()
        port_stats = port.read_port_stats()
        print(json.dumps(port_stats, indent=1))
        self.xm.session.start_traffic()
        time.sleep(2)
        port_stats = port.read_port_stats()
        print(json.dumps(port_stats, indent=1))
        assert(abs(port_stats['pt_total']['packets'] - port_stats['pr_total']['packets']) < 10)
        assert(abs(1000 - port.streams[0].read_stats()['pps']) < 10)
        assert(abs(1000 - port.tplds[0].read_stats()['pr_tpldtraffic']['pps']) < 10)
        self.xm.session.stop_traffic()
        self.xm.session.clear_stats()
        self.xm.session.start_traffic(blocking=True)

        ports_stats = XenaPortsStats(self.xm.session)
        ports_stats.read_stats()
        print(ports_stats.statistics.dumps())
        print(json.dumps(ports_stats.get_flat_stats(), indent=1))

        streams_stats = XenaStreamsStats(self.xm.session)
        streams_stats.read_stats()
        print(streams_stats.statistics.dumps())
        print(json.dumps(streams_stats.get_flat_stats(), indent=1))

        tplds_stats = XenaTpldsStats(self.xm.session)
        tplds_stats.read_stats()
        print(tplds_stats.statistics.dumps())
        print(json.dumps(tplds_stats.get_flat_stats(), indent=1))

    def test_stream_stats(self):
        """ For this tst we need back-to-back ports. """
        ports = self.xm.session.reserve_ports([self.port1, self.port2])
        ports[self.port1].load_config(path.join(path.dirname(__file__), 'configs', 'test_config_loopback.xpc'))
        ports[self.port1].set_attributes(p_loopback='NONE')
        ports[self.port2].load_config(path.join(path.dirname(__file__), 'configs', 'test_config.xpc'))

        self.xm.session.start_traffic(blocking=True)

        tpld_stats = XenaTpldsStats(self.xm.session)
        print(tpld_stats.read_stats().dumps())

        streams_stats = XenaStreamsStats(self.xm.session)
        statistics = streams_stats.read_stats()
        print(streams_stats.tx_statistics.dumps())
        print(statistics.dumps())

    def test_capture(self):
        port = self.xm.session.reserve_ports([self.port1])[self.port1]
        port.load_config(path.join(path.dirname(__file__), 'configs', 'test_config_loopback.xpc'))

        port.streams[0].set_attributes(ps_ratepps=10, ps_packetlimit=80)
        port.remove_stream(1)

        port.start_capture()
        port.start_traffic(blocking=True)
        port.stop_capture()
        packets = port.capture.get_packets()
        print(packets)
        assert(len(packets) == 80)
        for packet in packets:
            print(packet)
