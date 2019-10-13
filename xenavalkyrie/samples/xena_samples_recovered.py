"""
Setup:
Two Xena ports connected back to back.
Author: Lonnie Hailey
notes:
  1. time.sleep(40) # usage
  2. pymsgbox.alert('Enable Stream(%d)'  % sid, stream) # popup box usage
  3. Xena stream state cannot be set to "Supressed"
  4. Xena module 3 must be "Released"
  5. Xena stream "Stop" field be set to "10"
"""

from os import path
import sys
import logging
import json
import binascii
import csv
import pyperclip

from pypacker.layer12.ethernet import Ethernet, Dot1Q
from pypacker.layer3.ip6 import IP6
from pypacker.layer4.tcp import TCP

from trafficgenerator.tgn_utils import ApiType
from xenavalkyrie.xena_app import init_xena
from xenavalkyrie.xena_statistics_view import XenaPortsStats, XenaStreamsStats, XenaTpldsStats
from xenavalkyrie.xena_port import XenaCaptureBufferType
from xenavalkyrie.xena_tshark import Tshark, TsharkAnalyzer
import time
import pymsgbox

from time import ctime

wireshark_path = '/usr/bin'

from inspect import currentframe

###################################################################
#add ip address, port #, owner
###################################################################
api = ApiType.socket
chassis = '176.22.65.117'
port0 = chassis + '/' + '0/1'
port1 = chassis + '/' + '0/0'
owner = 'Python'
config0 = path.join(path.dirname(__file__), 'configs', 'test_config_1.xpc')
save_config = path.join(path.dirname(__file__), 'configs', 'save_config.xpc')
pcap_file = path.join(path.dirname(__file__), 'configs', 'xena_cap.pcap')
ports = {}

#: :type xm: xenavalkyrie.xena_app.XenaApp
xm = None

gui_state_to_cli_state = {'enabled': 'on',
                          'disabled': 'off'}


###################################################################
#nice code to get the current line number
def get_linenumber():
    cf = currentframe()
    #usage: pymsgbox.alert(get_linenumber(), 'Line number')
    #time.sleep(40)
    return cf.f_back.f_lineno

###################################################################

def connect():
    global xm

    # Log commands
    logger = logging.getLogger('log')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))

    # Create XenaApp object and connect to chassis.
    xm = init_xena(api, logger, owner, chassis)
    xm.session.add_chassis(chassis)

def disconnect():
    #Disconnect from chassis
    xm.session.disconnect()

def inventory():
    xm.session.inventory()
    print('+++')
    for c_name, chassis in xm.session.chassis_list.items():
        print('chassis ' + c_name)
        for m_name, module in chassis.modules.items():
            print('\tmodule ' + str(m_name))
            for p_name, port in module.ports.items():
                print('\t\tport ' + str(p_name))
                for s_name, _ in port.streams.items():
                    print('\t\t\tstream ' + str(s_name))
    print('+++')

def reserve():
    """ Reserve ports.
        Wait for ports up.
        Load configuration on one port.
        Build configuration on the second port.
    """

    global ports

    # reserve port 0
    ports = xm.session.reserve_ports([port1], force=True, reset=False)
    ports[port1].wait_for_up(10)

def configuration():

    # Load configuration on port-0.
    ports[port1].load_config(config0)

    # Get port-0/stream-0 object.
    p0_s0 = ports[port1].streams[0]

    # Get Multi-parameter query with get_attributes which returns all attributes values as dict.
    ps_config = p0_s0.get_attributes()
    print('{} info:\n{}'.format(p0_s0.name, json.dumps(ps_config, indent=1)))

    # Get packet headers.
    headers = p0_s0.get_packet_headers()
    print('{} headers:\n{}'.format(p0_s0.name, headers))
    # Access any header and field by name with nice string representation.
    print('{} MAC SRC: {}'.format(p0_s0.name, headers.src_s))
    print('{} VLAN ID: {}'.format(p0_s0.name, headers.vlan[0].vid))
    print('{} IP DST: {}'.format(p0_s0.name, headers.ip.dst_s))

    # Add stream on port-1
    p1_s0 = ports[port1].add_stream('new stream')

    # Set ps_packetlimit and ps_ratepps with set_attributes which sets list of attributes.
    p1_s0.set_attributes(ps_packetlimit=80, ps_ratepps=10)

    # Get single parameter query with get_attribute which returns the attribute value as str.
    ps_packetlimit = p1_s0.get_attribute('ps_packetlimit')
    ps_ratepps = p1_s0.get_attribute('ps_ratepps')
    print('{} info:\nps_packetlimit: {}\nps_ratepps: {}'.format(p1_s0.name, ps_packetlimit, ps_ratepps))

    # Set headers - all fields can be set with the constructor or by direct access after creation.
    eth = Ethernet(src_s='22:22:22:22:22:22')
    eth.dst_s = '11:11:11:11:11:11'
    vlan = Dot1Q(vid=17)
    eth.vlan.append(vlan)
    # In order to add header simply concatenate it.
    ip6 = IP6()
    tcp = TCP()
    headers = eth + ip6 + tcp
    p1_s0.set_packet_headers(headers)

    # Add modifier - all parameters can be set with the constructor or by direct access after creation.
    modifier = p1_s0.add_modifier(position=4)
    modifier.min_val = 100
    modifier.max_val = 200

    # Save new configuration.
    ports[port1].save_config(save_config)

def traffic():
    ###################################################################
    # START TEST CASE
    # Enable stream
    ###################################################################

    #Prerequisite: Loop streams and set enable to off
    for stream in ports[port1].streams.values():
        stream.set_attributes(PS_ENABLE='OFF')

    # this will print one time
    print ('Disable streams', get_linenumber())

    #Start test here - this will get the stream name and number
    for sid, stream in ports[port1].streams.items():
        stream.set_attributes(PS_ENABLE='ON')
        xm.session.clear_stats()
        xm.session.start_capture()
        xm.session.start_traffic(blocking=True)
        time.sleep(3)
        xm.session.stop_capture()

        # Get port level statistics.
        ports_stats = XenaPortsStats(xm.session)
        ports_stats.read_stats()
        print(ports_stats.statistics.dumps())

        # Get stream level statistics.
        streams_stats = XenaStreamsStats(xm.session)
        streams_stats.read_stats()

        #################################################################################################################
        #print counters
        print('TX packets = {}'.format(streams_stats.statistics[stream.name]['tx']['packets']))
        print('RX packets = {}'.format(streams_stats.statistics[stream.name]['rx']['pr_tpldtraffic']['pac']))
        print('TX bytes = {}'.format(streams_stats.statistics[stream.name]['tx']['bytes']))
        print('RX bytes = {}'.format(streams_stats.statistics[stream.name]['rx']['pr_tpldtraffic']['byt']))

        #verify tx counters
        text_file = open('c:/temp/somefile.txt', 'w')
        text_file.write('Stream(%s)' % sid)
        text_file.write('\nCounters for stream(%s)' %stream)
        text_file.write('\nTX packets = {}'.format(streams_stats.statistics[stream.name]['tx']['packets']))
        text_file.write('\nRX packets = {}'.format(streams_stats.statistics[stream.name]['rx']['pr_tpldtraffic']['pac']))
        text_file.write('\nTX bytes = {}'.format(streams_stats.statistics[stream.name]['tx']['bytes']))
        text_file.write('\nRX bytes = {}'.format(streams_stats.statistics[stream.name]['rx']['pr_tpldtraffic']['byt']))
        text_file.close()


        #################################################################################################################
        #
        # pyperclip to somefile.txt
        #
        #################################################################################################################

        text_file = open('c:/temp/somefile.txt', 'r').read()
        pyperclip.copy(text_file)


        # QTP click stream pop-up
        # pymsgbox.alert('get_counters for index (%d)' %sid, stream)
        # pymsgbox.alert('get_counters for index %d' % sid)
        # pymsgbox.alert('get_counters for index %s' % stream)

        # pymsgbox.alert('Enable Stream %s' % stream)  # popup box usage
        pymsgbox.alert(' %s' % stream)  # popup box usage

        #################################################################################################################
        #
        # pyperclip to capture.raw
        #
        #################################################################################################################

        # wireshark capture save to file

        # ok = time.strftime("%Y%m%d-%H%M%S")

        # fff = ('Counters for stream(%s)' % stream)
        mycapture = '%s' % stream

        text = ports[port1].capture.get_packets(to_index=1, cap_type=XenaCaptureBufferType.raw, file_name='c:/temp/mycapture.raw')
        text2 = ports[port1].capture.get_packets(to_index=1, cap_type=XenaCaptureBufferType.text, file_name='c:/temp/mycapture_' + mycapture + '.raw')
        # text2 = ports[port1].capture.get_packets(to_index=1, cap_type=XenaCaptureBufferType.text, file_name='c:/temp/mycapture_' + fff + '.raw')


        # pyperclip to mycapture.raw
        text_file = open('c:/temp/mycapture.raw', 'r').read()
        pyperclip.copy(text_file)

        # pymsgbox.alert('get_counters for index (%d)' % sid, stream)
        # pymsgbox.alert('get_counters for index (%s)' % stream)

        #turn stream off
        try:
            stream.set_attributes(PS_ENABLE='OFF')
        except Exception as _:
            stream.set_attributes(PS_ENABLE='OFF')

        #continue to next stream
        pymsgbox.alert('Next', 'Go to next stream')
    return

def run_all():
    connect()
    # inventory()
    reserve()
    # configuration()
    traffic()
    # i added this but traffic did not stop
    # xm.session.stop_traffic(blocking=True)
    disconnect()

if __name__ == '__main__':
    run_all()
