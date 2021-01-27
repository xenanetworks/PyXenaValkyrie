
import copy
import os
import subprocess
import sys
from typing import Optional


class Tshark:

    def __init__(self, ws_path: str, temp_folder: Optional[str] = None) -> None:
        """ Test if wireshark is installed and make sure temporary folder exists.

        :param ws_path: full path to wireshark installation folder.
        :param temp_folder: folder to save temporary files. If None - use OS 'native' temp folder.
        """
        if not os.path.exists(ws_path):
            raise FileNotFoundError(f'Wireshark installation not found at {ws_path}')
        self.ws_path = ws_path
        if not temp_folder:
            temp_folder = 'c:/temp' if sys.platform == 'win32' else '/tmp'
        self.temp_folder = temp_folder

    def text_to_pcap(self, text_file, pcap_file=None):
        text2pcap_call = [os.path.join(self.ws_path, 'text2pcap' + ('.exe' if sys.platform == 'win32' else ''))]
        text2pcap_call.append(text_file)
        if not pcap_file:
            pcap_file = os.path.splitext(text_file)[0] + '.pcap'
        text2pcap_call.append(pcap_file)
        subprocess.call(text2pcap_call)

    def analyze(self, pcap_file, analyser):
        tshark_path = os.path.join(self.ws_path, 'tshark' + ('.exe' if sys.platform == 'win32' else ''))
        tshark_call = analyser.build_tshark_call(tshark_path, pcap_file)
        out_file_name = self.temp_folder + '/' + os.path.basename(pcap_file) + '.txt'
        out_file = open(out_file_name, 'wb')
        if subprocess.call(tshark_call, stdout=out_file) > 0:
            raise Exception('{} - failed'.format(' '.join(tshark_call)))
        out_file.close()
        fields = analyser.process_out_file(out_file_name)
        os.remove(out_file_name)
        return fields


class TsharkAnalyzer:

    delimeter = '~'

    def __init__(self):
        self.read_filter = None
        self.fields = []

    def set_read_filter(self, read_filter):
        self.read_filter = read_filter

    def add_field(self, field):
        self.fields.append(field)

    def build_tshark_call(self, tshark_path, file_path):
        tsharkCall = []
        tsharkCall.append(tshark_path)
        tsharkCall.append('-r')
        tsharkCall.append(file_path)
        if self.read_filter:
            tsharkCall.append('-Y')
            tsharkCall.append(self.read_filter)
        if self.fields:
            tsharkCall.append('-T')
            tsharkCall.append('fields')
            for field in self.fields:
                tsharkCall.append('-e')
                tsharkCall.append(field)
                tsharkCall.append('-E')
                tsharkCall.append('aggregator=' + self.delimeter)
        return tsharkCall

    def process_multiple_results(self, results_str):
        results_list = results_str.split(self.delimeter)
        return results_list if len(results_list) else [results_str]

    def process_out_file(self, path):
        capture_fields = []
        tsharkin = open(path, "r")
        for line in tsharkin.readlines():
            fieldsValues = line.split('\t')
            packet_fields = {}
            for i in range(len(self.fields)):
                result = (copy.copy(fieldsValues[i])).replace('\n', "")
                result = self.process_multiple_results(result)
                packet_fields[self.fields[i]] = result
            capture_fields.append(packet_fields)
        return capture_fields
