

import binascii

import pandas as pd

from scapy.all import *
from scapy.contrib.mac_control import *

from xenavalkyrie.xena_port import XenaCaptureBufferType

import logging

logger = logging.getLogger(__name__)

def get_packets_df(capture, from_index, to_index, validate_l4_sum=False):
  """ Get captured packets from chassis as a Pandas dataframe object.

  :param from_index: index of first packet to read.
  :param to_index: index of last packet to read. If None - read all packets.

  :return: Pandas DataFrame of requested packets
  """

  to_index = to_index if to_index else len(capture.packets)

  df_cols = ['abs_time', 'latency', 'ifg', 'length', 
             'vlan', 'pcp', 'ether_type', 'mac_ctrl_op',
             'cos_enabled', 'c0_pause_time', 'c1_pause_time', 'c2_pause_time','c3_pause_time', 'c4_pause_time', 'c5_pause_time', 'c6_pause_time','c7_pause_time', 
             'l4_proto', 'recv_ip_sum', 'calc_ip_sum', 'recv_tcp_sum', 'calc_tcp_sum', 'recv_udp_sum', 'calc_udp_sum']
  df_data = []

  packets       = [binascii.unhexlify(p.split('0x')[-1]) for p in capture.get_packets(from_index, to_index, cap_type=XenaCaptureBufferType.raw)]
  packets_extra = [p.split("]")[-1].strip() for p in capture.get_packets_extra(from_index, to_index)]

  for index, data in enumerate(packets):

      vlan          = False
      pcp           = 0
      mac_ctrl_op   = 0
      cos_enabled   = 0
      c0_pause_time = 0
      c1_pause_time = 0
      c2_pause_time = 0
      c3_pause_time = 0
      c4_pause_time = 0
      c5_pause_time = 0
      c6_pause_time = 0
      c7_pause_time = 0
      l4_proto      = 0
      recv_ip_sum   = 0
      calc_ip_sum   = 0
      recv_tcp_sum  = 0
      calc_tcp_sum  = 0
      recv_udp_sum  = 0
      calc_udp_sum  = 0

      packet = Ether(data)

      try:
        if packet[Dot1Q]:
          vlan = True
      except Exception as e:
        pass

      if vlan:
        pcp        = packet[Dot1Q].prio
        ether_type = packet[Dot1Q].type
      else:
        ether_type = packet.type
      
      if ether_type == 0x8808:
        mac_ctrl_op = packet[MACControl]._op_code

        if packet[MACControl]._op_code == 0x0101:
          cos_enabled   = (packet[MACControl].c7_enabled << 7) | (packet[MACControl].c6_enabled << 6) | (packet[MACControl].c5_enabled << 5) | (packet[MACControl].c4_enabled << 4) | \
                          (packet[MACControl].c3_enabled << 3) | (packet[MACControl].c2_enabled << 2) | (packet[MACControl].c1_enabled << 1) | (packet[MACControl].c0_enabled << 0) 
          c0_pause_time = packet[MACControl].c0_pause_time
          c1_pause_time = packet[MACControl].c1_pause_time
          c2_pause_time = packet[MACControl].c2_pause_time
          c3_pause_time = packet[MACControl].c3_pause_time
          c4_pause_time = packet[MACControl].c4_pause_time
          c5_pause_time = packet[MACControl].c5_pause_time
          c6_pause_time = packet[MACControl].c6_pause_time
          c7_pause_time = packet[MACControl].c7_pause_time

      if ether_type == 0x0800:
        recv_ip_sum = packet[IP].chksum
        del packet[IP].chksum

        if packet[IP].proto == 0x6:
          l4_proto     = 0x6
          recv_tcp_sum = packet[TCP].chksum
          del packet[TCP].chksum
          packet = packet.__class__(bytes(packet))

          calc_ip_sum  = packet[IP].chksum
          calc_tcp_sum = packet[TCP].chksum

        elif packet[IP].proto == 0x11:
          l4_proto     = 0x11
          recv_udp_sum = packet[UDP].chksum
          del packet[UDP].chksum
          packet = packet.__class__(bytes(packet))

          calc_ip_sum  = packet[IP].chksum
          calc_udp_sum = packet[UDP].chksum

        else:
          packet = packet.__class__(bytes(packet))
          calc_ip_sum  = packet[IP].chksum

                                      
      df_data.append([int(i) for i in packets_extra[index].split(" ")] + 
                     [vlan, pcp, "{0:#0{1}x}".format(ether_type,6), "{0:#0{1}x}".format(mac_ctrl_op,6)] + 
                     [cos_enabled, c0_pause_time, c1_pause_time, c2_pause_time, c3_pause_time, c4_pause_time, c5_pause_time, c6_pause_time, c7_pause_time] +
                     [l4_proto, recv_ip_sum, calc_ip_sum, recv_tcp_sum, calc_tcp_sum, recv_udp_sum, calc_udp_sum])


  df = pd.DataFrame(df_data, columns=df_cols)
  df["pcp"].round().astype(int)
  df.insert(1,'delta',df['abs_time'].diff())
  df.insert(1,'rel_time', df.loc[1:, 'abs_time'] - df.at[0, 'abs_time'])
  df[['rel_time','delta']] = df[['rel_time','delta']].fillna(value=0)

  #logger.info(df[['abs_time', 'latency', 'length', 'vlan', 'pcp', 'ether_type', 'l4_proto', 'recv_ip_sum', 'calc_ip_sum', 'recv_tcp_sum', 'calc_tcp_sum', 'recv_udp_sum', 'calc_udp_sum']])
  return df