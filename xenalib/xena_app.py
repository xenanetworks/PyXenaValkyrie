
from trafficgenerator.tgn_app import TgnApp
from xenalib.api.XenaSocket import XenaSocket
from xenalib.api.KeepAliveThread import KeepAliveThread
from xenalib.xena_object import XenaObject
from xenalib.xena_port import XenaPort


def init_xena(logger):
    """ Create Xena manager object.

    :param logger: python logger object
    :return: Xena object
    """

    return XenaApp(logger)


class XenaApp(TgnApp):

    def __init__(self, logger):
        self.logger = logger
        self.session = XenaSession(self.logger)

    def add_chassis(self, chassis, owner, password='xena'):
        self.session.add_chassis(chassis, owner, password)

    def disconnect(self):
        self.session.disconnect()


class XenaSession(XenaObject):

    def __init__(self, logger):
        self.logger = logger
        self.api = None
        super(self.__class__, self).__init__(objType='session', index='', parent=None)

    def add_chassis(self, chassis, owner, password='xena'):
        XenaChassis(chassis, self).logon(owner, password)

    def disconnect(self):
        self.release_ports()
        for chassis in self.get_objects_by_type('chassis'):
            chassis.disconnect()

    def inventory(self):
        for chassis in self.get_objects_by_type('chassis'):
            chassis.inventory()

    def reserve_ports(self, locations, force=False):
        """ Reserve ports and reset factory defaults.

        :param locations: list of ports locations in the form <ip/slot/port> to reserve
        :param force: True - take forcefully, False - fail if port is reserved by other user
        :return: ports dictionary (index: object)
        """

        for location in locations:
            chassis = location.split('/')[0]
            port = XenaPort(location=location, parent=self, api=self.get_object_by_name(chassis).api)
            port.reserve(force)
            port.reset()

        return self.ports

    def release_ports(self):
        for port in self.ports.values():
            port.release()

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

        return {str(p): p for p in self.get_objects_by_type('port')}


class XenaChassis(XenaObject):

    def __init__(self, ip, parent):
        super(self.__class__, self).__init__(objType='chassis', index='', parent=parent, name=ip)

        self.api = XenaSocket(self.logger, ip)
        self.api.connect()
        self.keep_alive_thread = KeepAliveThread(self.api)
        self.keep_alive_thread.start()

    def logon(self, owner, password):
        self.send_command('c_logon', '"{}"'.format(password))
        self.send_command('c_owner', '"{}"'.format(owner))

    def disconnect(self):
        self.api.disconnect()

    def inventory(self):
        self.c_info = self.get_attributes('c_info')
        for m_index, m_portcounts in enumerate(self.c_info['c_portcounts'].split()):
            if int(m_portcounts):
                XenaModule(index=m_index, parent=self).inventory()

    @property
    def modules(self):
        """
        :return: dictionary {index: object} of all modules.
        """

        return {int(c.ref): c for c in self.get_objects_by_type('module')}


class XenaModule(XenaObject):

    def __init__(self, index, parent):
        super(self.__class__, self).__init__(objType='module', index=index, parent=parent)

    def inventory(self):
        self.m_info = self.get_attributes('m_info')
        if 'NOTCFP' in self.m_info['m_cfptype']:
            m_portcount = int(self.get_attribute('m_portcount'))
        else:
            m_portcount = int(self.get_attribute('m_cfpconfig').split()[0])
        for p_index in range(m_portcount):
            XenaPort(location='_/{}/{}'.format(self.ref, p_index), parent=self, api=self.api).inventory()

    @property
    def ports(self):
        """
        :return: dictionary {index: object} of all ports.
        """

        return {int(p.ref.split('/')[1]): p for p in self.get_objects_by_type('port')}
