
import time

from trafficgenerator.tgn_app import TgnApp
from xenalib.api.XenaSocket import XenaSocket
from xenalib.api.KeepAliveThread import KeepAliveThread
from xenalib.xena_object import XenaObject
from xenalib.xena_port import XenaPort


def init_xena(logger, host):
    """ Create Xena manager object.

    :param logger: python logger object
    :param host: chassis IP address
    :return: Xena object
    """

    xsocket = XenaSocket(logger, host)
    xsocket.connect()

    return XenaApp(logger, xsocket)


class XenaApp(TgnApp):

    def __init__(self, logger, xsocket):
        self.api = xsocket
        self.logger = logger
        self.session = XenaSession(xsocket, logger)
        self.chassis = XenaChassis(xsocket, logger)
        self.keep_alive_thread = KeepAliveThread(self.api)
        self.keep_alive_thread.start()

    def connect(self, owner, password='xena'):
        self.session.logon(owner, password)


class XenaSession(XenaObject):

    def __init__(self, xsocket, logger):
        self.api = xsocket
        self.logger = logger
        super(self.__class__, self).__init__(objType='session', index='', parent=None)

    def logon(self, owner, password):
        self.send_command('c_logon', '"{}"'.format(password))
        self.send_command('c_owner', '"{}"'.format(owner))

    def reserve_ports(self, ports_locations, force=False):
        """ Reserve ports and reset factory defaults.

        :param locations: list of ports locations in the form <ip/slot/port> to reserve
        :param force: True - take forcefully, False - fail if port is reserved by other user
        :return: ports dictionary (index: object)
        """

        for port_location in ports_locations:
            _, module, port = port_location.split('/')
            port = XenaPort(index='{}/{}'.format(module, port), parent=self)
            port.reserve(force)
            port.reset()

        return self.ports

    def release_ports(self):
        for port in self.ports.values():
            port.release()

    @property
    def ports(self):
        """
        :return: dictionary {index: object} of all ports.
        """

        return {int(p.ref.split('/')[1]): p for p in self.get_objects_by_type('port')}


class XenaChassis(XenaObject):

    def __init__(self, xsocket, logger):
        self.api = xsocket
        self.logger = logger
        super(self.__class__, self).__init__(objType='chassis', index='', parent=None)

    def inventory(self):
        self.c_info = self.get_attributes('c_info')
        for m_index, m_portcounts in enumerate(self.c_info['c_portcounts'].split()):
            if int(m_portcounts):
                XenaModule(index=m_index, parent=self).inventory()
        return self.modules

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
            print m_portcount
        for p_index in range(m_portcount):
            XenaPort(index='{}/{}'.format(self.ref, p_index), parent=self).inventory()
        return self.ports

    @property
    def ports(self):
        """
        :return: dictionary {index: object} of all ports.
        """

        return {int(p.ref.split('/')[1]): p for p in self.get_objects_by_type('port')}
