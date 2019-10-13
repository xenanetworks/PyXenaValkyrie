
from copy import deepcopy

from pypacker.layer12.ethernet import Ethernet, Dot1Q
from pypacker.layer3.ip6 import IP6
from pypacker.layer4.tcp import TCP


pypacker_2_xena = {'ethernet': 'ethernet',
                   'arp': 'arp',
                   'ip': 'ip',
                   'ip6': 'ipv6',
                   'udp': 'udp',
                   'tcp': 'tcp',
                   'icmp': 'icmp',
                   'dhcp': '39'
                   }


eth = Ethernet(src_s='22:22:22:22:22:22')
eth.dst_s = '11:11:11:11:11:11'
vlan = Dot1Q(vid=17, prio=3)
eth.vlan.append(vlan)
ip6 = IP6()
tcp = TCP()
headers = eth + ip6 + tcp
body_handler = deepcopy(headers)
ps_headerprotocol = []
while body_handler:
    segment = pypacker_2_xena.get(str(body_handler).split('(')[0].lower(), None)
    if not segment:
        print('pypacker header {} not in conversion list'.format(str(body_handler).split('(')[0].lower()))
        break
    ps_headerprotocol.append(segment)
    if type(body_handler) is Ethernet and body_handler.vlan:
        ps_headerprotocol.append('vlan')
    body_handler = body_handler.body_handler
