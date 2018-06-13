"""
Classes and utilities that represents Xena statistics as tables like the GUI.

Statistics views represent statistics as tables.
There are three different views - ports, streams and TPLD.

:author: yoram@ignissoft.com
"""

from collections import OrderedDict

from trafficgenerator.tgn_object import TgnObjectsDict


class XenaStats(object):
    """ Base class for all statistics views. """

    def __init__(self, session):
        """
        :param session: current session
        :type session: xenamanager.xena_app.XenaSession
        """

        self.session = session
        self.statistics = None

    def get_flat_stats(self):
        """
        :return: statistics as flat table {port/strea,/tpld name {group_stat name: value}}
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

    def read_stats(self):
        """ Read current ports statistics from chassis.

        :return: dictionary {port name {group name, {stat name: stat value}}}
        """

        self.statistics = TgnObjectsDict()
        for port in self.session.ports.values():
            self.statistics[port] = port.read_port_stats()
        return self.statistics


class XenaStreamsStats(XenaStats):
    """ Streams statistics view.

    Represents all streams statistics as table:

    +--------+-------+-----+-------+-----+-------+-----+-------+-----+-------+-----+
    | Stream | tx    |     | rx    |     |       |     |       |     |       |     |
    +--------+-------+-----+-------+-----+-------+-----+-------+-----+-------+-----+
    |        |       |     | TPLD  |     |       |     | TPLD  |     |       |     |
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

        self.tx_statistics = TgnObjectsDict()
        for port in self.session.ports.values():
            for stream in port.streams.values():
                self.tx_statistics[stream] = stream.read_stats()

        tpld_statistics = XenaTpldsStats(self.session).read_stats()

        self.statistics = TgnObjectsDict()
        for stream, stream_stats in self.tx_statistics.items():
            self.statistics[stream] = OrderedDict()
            self.statistics[stream]['tx'] = stream_stats
            self.statistics[stream]['rx'] = OrderedDict()
            stream_tpld = stream.get_attribute('ps_tpldid')
            for tpld, tpld_stats in tpld_statistics.items():
                if tpld.id == stream_tpld:
                    self.statistics[stream]['rx'][tpld] = tpld_stats
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

    def read_stats(self):
        """ Read current statistics from chassis.

        :return: dictionary {tpld full index {group name {stat name: stat value}}}
        """

        self.statistics = TgnObjectsDict()
        for port in self.session.ports.values():
            for tpld in port.tplds.values():
                self.statistics[tpld] = tpld.read_stats()
        return self.statistics
