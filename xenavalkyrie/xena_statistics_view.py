"""
Classes and utilities that represents Xena statistics as tables like the GUI.

Statistics views represent statistics as tables.
There are three different views - ports, streams and TPLD.

:author: yoram@ignissoft.com
"""
from collections import OrderedDict
from typing import Optional

from trafficgenerator.tgn_object import TgnSubStatsDict
from xenavalkyrie.xena_object import XenaObjectsDict, XenaObject
from xenavalkyrie.xena_app import XenaSession


class XenaStats:
    """ Base class for all statistics views. """

    def __init__(self, session: Optional[XenaSession] = XenaObject.session) -> None:
        """
        :param session: Deprecated.
        """
        self.statistics = None

    def get_flat_stats(self) -> OrderedDict:
        """ Returns statistics as flat table {port/stream/tpld name {group_stat name: value}}.

        :TODO: Works only for port statistics. Fix.
        """
        flat_stats = OrderedDict()
        for obj, port_stats in self.statistics.items():
            flat_obj_stats = OrderedDict()
            for group_name, group_values in port_stats.items():
                for stat_name, stat_value in group_values.items():
                    full_stat_name = group_name + '_' + stat_name
                    flat_obj_stats[full_stat_name] = stat_value
            flat_stats[obj.name] = flat_obj_stats
        return flat_stats
    flat_statistics = property(get_flat_stats)


class XenaPortsStats(XenaStats):
    """ Ports statistics view.

    Represents all ports statistics as multi table:

    +----------------+-------+-------+-----+-------+-------+-----+-----+
    | Port Name      | Group |       |     | Group |       |     | ... |
    +----------------+-------+-------+-----+-------+-------+-----+-----+
    |                | Name  | Name  | ... | Name  | Name  | ... | ... |
    +================+=======+=======+=====+=======+=======+=====+=====+
    | IP/Module/Port | value | value | ... | Name  | Name  | ... | ... |
    +----------------+-------+-------+-----+-------+-------+-----+-----+
    | IP/Module/Port | value | value | ... | Name  | Name  | ... | ... |
    +----------------+-------+-------+-----+-------+-------+-----+-----+
    """

    def read_stats(self) -> XenaObjectsDict:
        """ Read current ports statistics from chassis.

        :return: dictionary {port name {group name, {stat name: stat value}}}
        """
        self.statistics = XenaObjectsDict()
        for port in XenaSession.session.ports.values():
            self.statistics[port] = port.read_port_stats()
        return self.statistics


class XenaStreamsStats(XenaStats):
    """ Streams statistics view.

    Represents all streams statistics as table:

    +--------+-------+-----+-------+-----+-------+-----+-------+-----+-------+-----+
    | Stream | tx    |     | rx    |     |       |     |       |     |       |     |
    +--------+-------+-----+-------+-----+-------+-----+-------+-----+-------+-----+
    |        |       |     | Port  |     |       |     | Port  |     |       |     |
    +--------+-------+-----+-------+-----+-------+-----+-------+-----+-------+-----+
    |        |       |     | Group |     | Group |     | Group |     | Group |     |
    +--------+-------+-----+-------+-----+-------+-----+-------+-----+-------+-----+
    |        | Name  | ... | Name  | ... | Name  | ... | Name  | ... | Name  | ... |
    +========+=======+=====+=======+=====+=======+=====+=======+=====+=======+=====+
    | Object | value | ... | value | ... | value | ... | value | ... | value | ... |
    +--------+-------+-----+-------+-----+-------+-----+-------+-----+-------+-----+
    | Object | value | ... | value | ... | value | ... | value | ... | value | ... |
    +--------+-------+-----+-------+-----+-------+-----+-------+-----+-------+-----+
    """

    def read_stats(self):
        """ Read current statistics from chassis.

        :return: dictionary {stream: {tx: {stat name: stat value}} rx: {tpld: {stat group {stat name: value}}}}
        """

        self.tx_statistics = XenaObjectsDict()
        for port in XenaObject.session.ports.values():
            for stream in port.streams.values():
                self.tx_statistics[stream] = stream.read_stats()

        tpld_statistics = XenaTpldsStats().read_stats()

        self.statistics = XenaObjectsDict()
        for stream, stream_stats in self.tx_statistics.items():
            self.statistics[stream] = OrderedDict()
            self.statistics[stream]['tx'] = stream_stats
            self.statistics[stream]['rx'] = TgnSubStatsDict()
            ps_tpldid = stream.get_attribute('ps_tpldid')
            stream_tpld = int(ps_tpldid) if ps_tpldid else -1
            for tpld, tpld_stats in tpld_statistics.items():
                if tpld.id == stream_tpld:
                    self.statistics[stream]['rx'][tpld.parent] = tpld_stats
        return self.statistics

    def get_flat_stats(self):
        return OrderedDict({str(k): v for k, v in self.tx_statistics.items()})


class XenaTpldsStats(XenaStats):
    """ TPLDs statistics view.

    Represents all TPLDs statistics as multi column table:

    +-------------------+-------+-------+-----+-------+-------+-----+-----+
    | TPLD Full Index   | Group |       |     | Group |       |     | ... |
    +-------------------+-------+-------+-----+-------+-------+-----+-----+
    |                   | Name  | Name  | ... | Name  | Name  | ... | ... |
    +===================+=======+=======+=====+=======+=======+=====+=====+
    | Module/Port/Index | value | value | ... | Name  | Name  | ... | ... |
    +-------------------+-------+-------+-----+-------+-------+-----+-----+
    | Module/Port/Index | value | value | ... | Name  | Name  | ... | ... |
    +-------------------+-------+-------+-----+-------+-------+-----+-----+
    """

    def read_stats(self) -> XenaObjectsDict:
        """ Read current statistics from chassis.

        :return: dictionary {tpld full index {group name {stat name: stat value}}}
        """
        self.statistics = XenaObjectsDict()
        for port in XenaObject.session.ports.values():
            for tpld in port.tplds.values():
                self.statistics[tpld] = tpld.read_stats()
        return self.statistics
