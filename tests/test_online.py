"""
Tests that require online ports.

Most tests use loopback port as this is the simplest configuration.
Some tests require two back-to-back ports, like stream statistics tests.

@author yoram@ignissoft.com
"""
import binascii
import json
import logging
from pathlib import Path

from pypacker.layer12 import ethernet

from xenavalkyrie.xena_app import XenaApp
from xenavalkyrie.xena_statistics_view import XenaPortsStats, XenaStreamsStats, XenaTpldsStats
from xenavalkyrie.xena_port import XenaCaptureBufferType
from xenavalkyrie.xena_tshark import Tshark, TsharkAnalyzer

WIRESHARK_PATH = 'C:/Program Files/Wireshark'


def test_online(xm: XenaApp, locations: dict, logger: logging.Logger) -> None:
    """ Reserve ports and wait for ports online. """
    logger.info(test_online.__doc__.strip())

    xm.session.reserve_ports(locations, force=False, reset=True)
    for port in xm.session.ports.values():
        port.wait_for_up(timeout=16)
    for port in xm.session.ports.values():
        assert port.is_online()


def test_gui_traffic(xm: XenaApp, locations: dict, logger: logging.Logger) -> None:
    """ Run traffic and test ports/streams/TPLD statistics. """
    logger.info(test_gui_traffic.__doc__.strip())

    xm.session.reserve_ports(locations, force=False, reset=True)
    port1 = xm.session.ports[locations[0]]
    port2 = xm.session.ports[locations[1]]
    port1.load_config(Path(__file__).parent.joinpath('configs', 'test_config_1.xpc'))
    port2.load_config(Path(__file__).parent.joinpath('configs', 'test_config_2.xpc'))

    xm.session.start_traffic(blocking=True)

    ports_stats = XenaPortsStats()
    ports_stats.read_stats()
    print(ports_stats.statistics.dumps(indent=2))
    assert ports_stats.statistics[port1]['pt_total']['packets'] == ports_stats.statistics[port2]['pr_total']['packets']
    ports_flat_stats = ports_stats.flat_statistics
    print(json.dumps(ports_flat_stats, indent=2))
    assert ports_flat_stats[port2.name]['pt_total_packets'] == ports_flat_stats[port1.name]['pr_total_packets']

    streams_stats = XenaStreamsStats()
    streams_stats.read_stats()
    print(streams_stats.statistics.dumps(indent=2))
    stream_0_0 = port1.streams[0]
    assert streams_stats.statistics[stream_0_0]['tx']['bytes'] == streams_stats.statistics[stream_0_0]['rx']['pr_tpldtraffic']['byt']
    assert streams_stats.statistics[stream_0_0]['tx']['bytes'] == streams_stats.statistics[stream_0_0]['rx'][port2]['pr_tpldtraffic']['byt']

    tpld_stats = XenaTpldsStats()
    tpld_stats.read_stats()
    print(tpld_stats.statistics.dumps(indent=2))
    tpld_0_0_0 = port2.tplds[0]
    assert streams_stats.statistics[stream_0_0]['tx']['bytes'] == tpld_stats.statistics[tpld_0_0_0.name]['pr_tpldtraffic']['byt']


def test_capture(xm: XenaApp, locations: dict, logger: logging.Logger) -> None:
    """ Run traffic and test capture. """
    logger.info(test_capture.__doc__.strip())

    xm.session.reserve_ports(locations, force=False, reset=True)
    port1 = xm.session.ports[locations[0]]
    port2 = xm.session.ports[locations[1]]
    port1.load_config(Path(__file__).parent.joinpath('configs', 'test_config_1.xpc'))

    port1.streams[0].set_attributes(ps_ratepps=10, ps_packetlimit=80)
    port1.remove_stream(1)

    port2.start_capture()
    port1.start_traffic(blocking=True)
    port2.stop_capture()

    packets = port2.capture.get_packets(0, 1, cap_type=XenaCaptureBufferType.raw)
    assert len(packets) == 1
    port2.capture.packets[0].get_attributes()
    packet = ethernet.Ethernet(binascii.unhexlify(packets[0]))
    assert packet.upper_layer.dst_s == '2.2.2.1'

    packets = port2.capture.get_packets(10, 20, cap_type=XenaCaptureBufferType.raw)
    print(packets[0])
    assert len(packets) == 10

    packets = port2.capture.get_packets(file_name=Path(__file__).parent.joinpath('temp', 'xena_cap.txt').as_posix())
    print(packets[0])
    assert len(packets) == 80

    tshark = Tshark(WIRESHARK_PATH)
    pcap_file = Path(__file__).parent.joinpath('temp', 'xena_cap.pcap')
    port2.capture.get_packets(cap_type=XenaCaptureBufferType.pcap, file_name=pcap_file.as_posix(), tshark=tshark)
    analyser = TsharkAnalyzer()
    analyser.add_field('ip.src')
    analyser.add_field('ip.dst')
    fields = tshark.analyze(pcap_file.as_posix(), analyser)
    print(fields)
    assert len(fields) == 80
