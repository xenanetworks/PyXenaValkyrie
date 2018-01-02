"""
Classes and utilities that represents Xena statistics as tables like the GUI.

Statistics views represent statistics as tables.
There are three different views - ports, streams and TPLD.

:author: yoram@ignissoft.com
"""

from collections import OrderedDict


class XenaStats(object):
    """ Base class for all statistics views. """

    def __init__(self, session):
        """
        :param session: current session
        :type session: xenamanager.xena_app.XenaSession
        """
        self.session = session


class XenaPortsStats(XenaStats):
    """ Ports statistics view.

    Represents all ports statistics as table:

    Port Name      | pt_total_pps | pt_total_packets | ...
    ---------------+--------------+------------------+----
    IP/Module/Port | value        | value            | ...
    IP/Module/Port | value        | value            | ...
    """

    def read_stats(self):
        """ Read current ports statistics from chassis.

        :return: dictionary <port name, <stat name, stat value>>
        """

        self.statistics = OrderedDict()
        for name, port in self.session.ports.items():
            port_stats = OrderedDict()
            for group_name, group in port.read_port_stats().items():
                for stat_name, value in group.items():
                    full_stat_name = group_name + '_' + stat_name
                    port_stats[full_stat_name] = value
            self.statistics[name] = port_stats
        return self.statistics


class XenaStreamsStats(XenaStats):
    """ Streams statistics view.

    Represents all streams statistics as table:

    Stream Full Index | pps   | packets | ...
    ------------------+-------+---------+----
    Module/Port/Index | value | value   | ...
    Module/Port/Index | value | value   | ...
    """

    def read_stats(self):
        """ Read current statistics from chassis.

        :return: dictionary <stream full index, <stat name, stat value>>
        """

        self.statistics = OrderedDict()
        for port in self.session.ports.values():
            for stream in port.streams.values():
                self.statistics[stream.ref] = stream.read_stats()
        return self.statistics


class XenaTpldsStats(XenaStats):
    """ TPLDs statistics view.

    Represents all TPLDs statistics as table:

    TPLD Full   Index | pr_tplderrors   | pr_tpldtraffic | ...
    ------------------+-----------------+----------------+----
    Module/Port/Index | value           | value          | ...
    Module/Port/Index | value           | value          | ...
    """

    def read_stats(self):
        """ Read current statistics from chassis.

        :return: dictionary <tpld full index, <stat name, stat value>>
        """

        self.statistics = OrderedDict()
        for port in self.session.ports.values():
            for tpld in port.tplds.values():
                self.statistics[tpld.ref] = tpld.read_stats()
        return self.statistics
