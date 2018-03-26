"""
Base class for all Xena package tests.

@author yoram@ignissoft.com
"""

import unittest

from xenamanager.xena_tshark import Tshark, TsharkAnalyzer

wireshark_path = 'E:/Program Files/Wireshark'


class XenaTestBase(unittest.TestCase):

    text_file = 'c:/temp/xena_cap.txt'

    def setUp(self):
        self.tshark = Tshark(wireshark_path)

    def tearDown(self):
        pass

    def test_to_pcap(self):
        self.tshark.text_to_pcap(self.text_file)

    def test_analyze(self):
        analyser = TsharkAnalyzer()
        analyser.add_field('ip.src')
        analyser.add_field('ip.dst')
        fields = self.tshark.analyze('c:/temp/xena_cap.pcap', analyser)
        print(fields)
        assert(len(fields) == 80)
        analyser.set_read_filter('ip.dst == 1.1.0.1')
        fields = self.tshark.analyze('c:/temp/xena_cap.pcap', analyser)
        print(fields)
        assert(len(fields) == 1)
        analyser.set_read_filter('ip.dst == 1.1.0.1 && frame.number >= 10')
        fields = self.tshark.analyze('c:/temp/xena_cap.pcap', analyser)
        print(fields)
        assert(len(fields) == 0)
