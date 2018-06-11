"""
Base class for all Xena package tests.

@author yoram@ignissoft.com
"""

from os import path

from trafficgenerator.test.test_tgn import TgnTest
from xenamanager.xena_tshark import Tshark, TsharkAnalyzer


class XenaTestBase(TgnTest):

    TgnTest.config_file = path.join(path.dirname(__file__), 'XenaManager.ini')

    text_file = path.join(path.dirname(__file__), 'configs', 'xena_cap.txt')
    pcap_file = path.join(path.dirname(__file__), 'configs', 'xena_cap.pcap')

    def setUp(self):
        self.temp_dir = self.config.get('General', 'temp_dir')
        self.tshark = Tshark(self.config.get('General', 'wireshark_dir'))

    def tearDown(self):
        pass

    def test_to_pcap(self):
        self.tshark.text_to_pcap(self.text_file)

    def test_analyze(self):
        analyser = TsharkAnalyzer()
        analyser.add_field('ip.src')
        analyser.add_field('ip.dst')
        fields = self.tshark.analyze(self.pcap_file, analyser)
        print(fields)
        assert(len(fields) == 80)
        analyser.set_read_filter('ip.dst == 1.1.0.1')
        fields = self.tshark.analyze(self.pcap_file, analyser)
        print(fields)
        assert(len(fields) == 1)
        analyser.set_read_filter('ip.dst == 1.1.0.1 && frame.number >= 10')
        fields = self.tshark.analyze(self.pcap_file, analyser)
        print(fields)
        assert(len(fields) == 0)
