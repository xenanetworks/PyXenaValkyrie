"""
Classes and utilities that represents Xena XenaManager-2G application and chassis.

:author: yoram@ignissoft.com
"""

from trafficgenerator.tgn_app import TgnApp
from xenamanager.api.XenaSocket import XenaSocket
from xenamanager.api.KeepAliveThread import KeepAliveThread
from xenamanager.xena_object import XenaObject
from xenamanager.xena_port import XenaPort


def init_xena(logger, owner):
    """ Create XenaManager object.

    :param logger: python logger
    :param owner: owner of the scripting session
    :return: Xena object
    """

    return XenaApp(logger, owner)


class XenaApp(TgnApp):
    """ XenaManager object, equivalent to XenaManager-2G application. """

    def __init__(self, logger, owner):
        """ Start XenaManager-2G equivalent application.

        :param logger: python logger
        :param owner: owner of the scripting session
        """

        self.logger = logger
        self.session = XenaSession(self.logger, owner)
        self.session.session = self.session

    def logoff(self):
        """ Exit the application. """

        self.session.disconnect()


class XenaSession(XenaObject):
    """ Xena scripting object. Root object for the Xena objects tree. """

    def __init__(self, logger, owner):
        """
        :param logger: python logger
        :param owner: owner of the scripting session
        """

        self.logger = logger
        self.owner = owner
        self.api = None
        super(self.__class__, self).__init__(objType='session', index='', parent=None)

    def add_chassis(self, chassis, password='xena'):
        """ Add chassis.

        XenaManager-2G -> Add Chassis.

        :param chassis: chassis IP address
        :param password: chassis password
        """

        if chassis not in self.chassis_list:
            XenaChassis(chassis, self).logon(password, self.owner)

    def disconnect(self):
        """ Disconnect from all chassis. """

        self.release_ports()
        for chassis in self.get_objects_by_type('chassis'):
            chassis.disconnect()

    def inventory(self):
        """ Get inventory for all chassis. """

        for chassis in self.get_objects_by_type('chassis'):
            chassis.inventory()

    def reserve_ports(self, locations, force=False):
        """ Reserve ports and reset factory defaults.

        XenaManager-2G -> Reserve/Relinquish Port.
        XenaManager-2G -> Reserve Port.

        :param locations: list of ports locations in the form <ip/slot/port> to reserve
        :param force: True - take forcefully, False - fail if port is reserved by other user
        :return: ports dictionary (index: object)
        """

        for location in locations:
            ip, module, port = location.split('/')
            self.chassis_list[ip].reserve_ports(['{}/{}'.format(module, port)], force)

        return self.ports

    def release_ports(self):
        """ Release all ports that were reserved during the session.

        XenaManager-2G -> Release Ports.
        """

        for chassis in self._per_chassis_ports(*self._get_operation_ports()):
            chassis.release_ports()

    def clear_stats(self, *ports):
        """ Clear stats (TX and RX) for list of ports.

        :param ports: list of ports to clear stats on. Default - all session ports.
        """

        for chassis, chassis_ports in self._per_chassis_ports(*self._get_operation_ports(*ports)).items():
            chassis.clear_stats(*chassis_ports)

    def start_traffic(self, blocking=False, *ports):
        """ Start traffic on list of ports.

        :param blocking: True - start traffic and wait until traffic ends, False - start traffic and return immediately.
        :param ports: list of ports to start traffic on. Default - all session ports.
        """

        for chassis, chassis_ports in self._per_chassis_ports(*self._get_operation_ports(*ports)).items():
            chassis.start_traffic(False, *chassis_ports)
        if blocking:
            for chassis, chassis_ports in self._per_chassis_ports(*self._get_operation_ports(*ports)).items():
                chassis.wait_traffic(*chassis_ports)

    def stop_traffic(self, *ports):
        """ Stop traffic on list of ports.

        :param ports: list of ports to stop traffic on. Default - all session ports.
        """

        for chassis, chassis_ports in self._per_chassis_ports(*self._get_operation_ports(*ports)).items():
            chassis.stop_traffic(*chassis_ports)

    #
    # Properties.
    #

    @property
    def chassis_list(self):
        """
        :return: dictionary {name: object} of all chassis.
        """

        return {str(c): c for c in self.get_objects_by_type('chassis')}

    @property
    def ports(self):
        """
        :return: dictionary {name: object} of all ports.
        """

        ports = {}
        for chassis in self.chassis_list.values():
            ports.update({str(p): p for p in chassis.get_objects_by_type('port')})
        return ports

    #
    # Private methods.
    #

    def _get_operation_ports(self, *ports):
        return ports if ports else self.ports.values()

    def _per_chassis_ports(self, *ports):
        per_chassis_ports = {}
        for port in ports:
            chassis = self.get_object_by_name(port.name.split('/')[0])
            if chassis not in per_chassis_ports:
                per_chassis_ports[chassis] = []
            per_chassis_ports[chassis].append(port)
        return per_chassis_ports


class XenaChassis(XenaObject):
    """ Represents single Xena chassis. """

    def __init__(self, ip, parent):
        super(self.__class__, self).__init__(objType='chassis', index='', parent=parent, name=ip)

        self.api = XenaSocket(self.logger, ip)
        self.api.connect()
        self.keep_alive_thread = KeepAliveThread(self.api)
        self.keep_alive_thread.start()

    def logon(self, password, owner):
        self.send_command('c_logon', '"{}"'.format(password))
        self.send_command('c_owner', '"{}"'.format(owner))

    def disconnect(self):
        self.api.disconnect()

    def inventory(self):
        """ Get chassis inventory. """

        c_info = self.get_attributes('c_info')
        for m_index, m_portcounts in enumerate(c_info['c_portcounts'].split()):
            if int(m_portcounts):
                XenaModule(index=m_index, parent=self).inventory()

    def reserve_ports(self, locations, force=False):
        """ Reserve ports and reset factory defaults.

        XenaManager-2G -> Reserve/Relinquish Port.
        XenaManager-2G -> Reset port.

        :param locations: list of ports locations in the form <slot/port> to reserve
        :param force: True - take forcefully, False - fail if port is reserved by other user
        :return: ports dictionary (index: object)
        """

        for location in locations:
            port = XenaPort(location=location, parent=self)
            port.reserve(force)
            port.reset()

        return self.ports

    def release_ports(self):
        """ Release all ports that were reserved during the session.

        XenaManager-2G -> Release Ports.
        """

        for port in self.ports.values():
            port.release()

    def start_traffic(self, blocking=False, *ports):
        self._traffic_command('on', *ports)
        if blocking:
            self.wait_traffic(*ports)

    def wait_traffic(self, *ports):
        for port in ports:
            port.wait_for_states('p_traffic', int(2.628e+6), 'off')

    def stop_traffic(self, *ports):
        self._traffic_command('off', *ports)

    def clear_stats(self, *ports):
        for port in ports:
            port.clear_stats()

    def _get_operation_ports(self, *ports):
        return ports if ports else self.ports.values()

    #
    # Properties.
    #

    @property
    def modules(self):
        """
        :return: dictionary {index: object} of all modules.
        """

        return {int(c.ref): c for c in self.get_objects_by_type('module')}

    @property
    def ports(self):
        """
        :return: dictionary {name: object} of all ports.
        """

        return {str(p): p for p in self.get_objects_by_type('port')}

    #
    # Private methods.
    #

    def _traffic_command(self, command, *ports):
        ports = self._get_operation_ports(*ports)
        ports_str = ' '.join([p.ref.replace('/', ' ') for p in ports])
        self.send_command('c_traffic', command, ports_str)
        for port in ports:
            port.wait_for_states('p_traffic', 40, command)


class XenaModule(XenaObject):
    """ Represents Xena module. """

    def __init__(self, index, parent):
        """
        :param index: module index, 0 based.
        :param parent: chassis object.
        """

        super(self.__class__, self).__init__(objType='module', index=index, parent=parent)

    def inventory(self):
        """ Get module inventory. """

        m_info = self.get_attributes('m_info')
        if 'NOTCFP' in m_info['m_cfptype']:
            a = self.get_attribute('m_portcount')
            m_portcount = int(a)
        else:
            m_portcount = int(self.get_attribute('m_cfpconfig').split()[0])
        for p_index in range(m_portcount):
            XenaPort(location='{}/{}'.format(self.ref, p_index), parent=self).inventory()

    #
    # Properties.
    #

    @property
    def ports(self):
        """
        :return: dictionary {index: object} of all ports.
        """

        return {int(p.ref.split('/')[1]): p for p in self.get_objects_by_type('port')}
