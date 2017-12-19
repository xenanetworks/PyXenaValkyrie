"""
Classes and utilities that represents Xena statistics as tables like the GUI.

:author: yoram@ignissoft.com
"""

from collections import OrderedDict


class XenaStats(object):

    def __init__(self, session):
        self.session = session


class XenaPortsStats(XenaStats):

    def read_stats(self):
        self.statistics = OrderedDict()
        for name, port in self.session.ports.items():
            port_stats = OrderedDict()
            for group_name, group in port.read_port_stats().items():
                for stat_name, value in group.items():
                    full_stat_name = group_name + '_' + stat_name
                    port_stats[full_stat_name] = value
            self.statistics[name] = port_stats
