from copy import deepcopy

from pypacker.layer12.ethernet import Dot1Q, Ethernet

packet_header = Ethernet()
packet_header.vlan.append(Dot1Q())
deepcopy(packet_header)
print(packet_header)
deepcopy(packet_header)
