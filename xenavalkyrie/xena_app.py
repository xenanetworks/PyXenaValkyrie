"""
Classes and utilities that represents Xena XenaManager-2G application and chassis.

:author: yoram@ignissoft.com
"""

from __future__ import annotations
from logging import Logger
import time
from typing import Optional, Union

from trafficgenerator.tgn_app import TgnApp
from trafficgenerator.tgn_utils import ApiType, TgnError
from xenavalkyrie.api.xena_rest import XenaRestWrapper
from xenavalkyrie.api.xena_cli import XenaCliWrapper
from xenavalkyrie.xena_object import XenaObject
from xenavalkyrie.xena_port import XenaPort


def init_xena(api: ApiType, logger: Logger, owner: str,
              ip: Optional[str] = None, port: Optional[int] = 57911) -> XenaApp:
    """ Create XenaApp object.

    :param api: cli/rest
    :param logger: python logger
    :param owner: owner of the scripting session
    :param ip: rest server IP
    :param port: rest server TCP port
    """
    if api == ApiType.socket:
        api_wrapper = XenaCliWrapper(logger)
    elif api == ApiType.rest:
        api_wrapper = XenaRestWrapper(logger, ip, port)
    else:
        raise TgnError(f'{api} API not supported, only {ApiType.socket} and {ApiType.rest}')
    return XenaApp(logger, owner, api_wrapper)


class XenaApp(TgnApp):
    """ XenaApp object, equivalent to XenaManager-2G application. """

    def __init__(self, logger: Logger, owner: str, api_wrapper: Union[XenaCliWrapper, XenaRestWrapper]) -> None:
        """ Start XenaManager-2G equivalent application.

        This seems somewhat redundant but we keep it for compatibility with all other TG packages.

        :param logger: python logger
        :param owner: owner of the scripting session
        :param api_wrapper: cli/rest API pbject.
        """
        super().__init__(logger, api_wrapper)
        self.session = XenaSession(logger, owner, api_wrapper)


class XenaSession(XenaObject):
    """ Xena scripting object. Root object for the Xena objects tree. """

    def __init__(self, logger, owner, api):
        """
        :param logger: python logger
        :param owner: owner of the scripting session
        :param api: cli/rest API pbject.
        """

        self.logger = logger
        self.api = api
        self.owner = owner

        super(self.__class__, self).__init__(objType='session', index='', parent=None, objRef=owner)
        self.session = self
        self.chassis = None
        self.api.connect(owner)

    def add_chassis(self, chassis, port=22611, password='xena'):
        """ Add chassis.

        XenaManager-2G -> Add Chassis.

        :param chassis: chassis IP address
        :param port: chassis port number
        :param password: chassis password
        :return: newly created chassis
        :rtype: xenavalkyrie.xena_app.XenaChassis
        """

        if chassis not in self.chassis_list:
            try:
                XenaChassis(self, chassis, port, password)
            except Exception as error:
                self.objects.pop('{}/chassis/{}'.format(self.owner, chassis))
                raise error
        return self.chassis_list[chassis]

    def disconnect(self):
        """ Release ports and disconnect from all chassis. """

        self.release_ports()
        self.api.disconnect()

    def inventory(self):
        """ Get inventory for all chassis. """

        for chassis in self.chassis_list.values():
            chassis.inventory(modules_inventory=True)

    def reserve_ports(self, locations, force=False, reset=True):
        """ Reserve ports and reset factory defaults.

        XenaManager-2G -> Reserve/Relinquish Port.
        XenaManager-2G -> Reserve Port.

        :param locations: list of ports locations in the form <ip/slot/port> to reserve
        :param force: True - take forcefully. False - fail if port is reserved by other user
        :param reset: True - reset port, False - leave port configuration
        :return: ports dictionary (index: object)
        """

        for location in locations:
            ip, module, port = location.split('/')
            self.chassis_list[ip].reserve_ports(['{}/{}'.format(module, port)], force, reset)

        return self.ports

    def release_ports(self):
        """ Release all ports that were reserved during the session.

        XenaManager-2G -> Release Ports.
        """

        for chassis in self._per_chassis_ports(*self._get_operation_ports()):
            chassis.release_ports()

    def start_traffic(self, blocking=False, *ports):
        """ Start traffic on list of ports.

        :param blocking: True - start traffic and wait until traffic ends, False - start traffic and return.
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

    def clear_stats(self, *ports):
        """ Clear stats (TX and RX) for list of ports.

        :param ports: list of ports to clear stats on. Default - all session ports.
        """

        for port in self._get_operation_ports(*ports):
            port.clear_stats()

    def start_capture(self, *ports):
        """ Start capture on list of ports.

        :param ports: list of ports to start capture on. Default - all session ports.
        """

        for port in self._get_operation_ports(*ports):
            port.start_capture()

    def stop_capture(self, *ports):
        """ Stop capture on list of ports.

        :param ports: list of ports to stop capture on. Default - all session ports.
        """

        for port in self._get_operation_ports(*ports):
            port.stop_capture()

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

    cli_prefix = 'c'

    _info_config_commands = ['c_info', 'c_config']
    stats_captions = ['ses', 'typ', 'adr', 'own', 'ops', 'req', 'rsp']

    def __init__(self, parent, ip, port=22611, password='xena'):
        """
        :param parent: parent session object
        :param owner: owner of the scripting session
        :param ip: chassis IP address
        :param port: chassis port number
        :param password: chassis password
        """

        super(self.__class__, self).__init__(objType='chassis', index='', parent=parent, name=ip,
                                             objRef='{}/chassis/{}'.format(parent.ref, ip))
        self.chassis = self
        self.owner = parent.owner
        self.ip = ip
        self.port = port
        self.password = password
        self.api.add_chassis(self)

        self.c_info = None

    def shutdown(self, restart=False, wait=False):
        """ Shutdown chassis.

        Limitations: shutdown to single chassis will disconnect all chassis so in multiple chassis environment the test
        should reconnect by calling api.add_chassis(chassis).

        :param restart: True - restart, False - poweroff
        :param wait: True - wait for chassis to come up after restart, False - return immediately
        :todo: fix limitation.
        """

        whattodo = 'restart' if restart else 'shutdown'
        self.send_command('c_down', '-1480937026', whattodo)
        self.api.disconnect()
        if wait:
            while True:
                time.sleep(2)
                try:
                    self.api.connect(self.owner)
                    self.api.add_chassis(self)
                    break
                except Exception as e:
                    pass

    def get_session_id(self):
        """ Get ID of the current automation session on the chassis.

        Note that this ID can be different for different chassis on the same session.

        :return: chassis ID.
        """

        raise NotImplementedError('Underlying CLI command c_stats returns internal error.')

    def inventory(self, modules_inventory=False):
        """ Get chassis inventory.

        :param modules_inventory: True - read modules inventory, false - don't read.
        """

        self.c_info = self.get_attributes()
        for m_index, m_portcounts in enumerate(self.c_info['c_portcounts'].split()):
            if int(m_portcounts):
                module = XenaModule(parent=self, index=m_index)
                if modules_inventory:
                    module.inventory()

    def reserve_ports(self, locations, force=False, reset=True):
        """ Reserve ports and reset factory defaults.

        XenaManager-2G -> Reserve/Relinquish Port.
        XenaManager-2G -> Reset port.

        :param locations: list of ports locations in the form <module/port> to reserve
        :param force: True - take forcefully, False - fail if port is reserved by other user
        :param reset: True - reset port, False - leave port configuration
        :return: ports dictionary (index: object)
        """

        for location in locations:
            port = XenaPort(parent=self, index=location)
            port.reserve(force)
            if reset:
                port.reset()

        return self.ports

    def release_ports(self):
        """ Release all ports that were reserved during the session.

        XenaManager-2G -> Release Ports.
        """

        for port in self.ports.values():
            port.release()

    def start_traffic(self, blocking=False, *ports):
        """ Start traffic on list of ports.

        :param blocking: True - start traffic and wait until traffic ends, False - start traffic and return.
        :param ports: list of ports to start traffic on. Default - all session ports.
        """

        self._traffic_command('on', *ports)
        if blocking:
            self.wait_traffic(*ports)

    def wait_traffic(self, *ports):
        """ Wait until traffic stops on ports.

        :param ports: list of ports to wait for.
        """

        for port in ports:
            port.wait_for_states('p_traffic', int(2.628e+6), 'off')

    def stop_traffic(self, *ports):
        """ Stop traffic on list of ports.

        :param ports: list of ports to stop traffic on. Default - all session ports.
        """

        self._traffic_command('off', *ports)

    def read_stats(self):
        """
        :return: dictionary {own: {stat name: value}}
        """
        raise NotImplementedError('Bug in chassis when trying to read c_statsession')

    def save_config(self, config_file_name):
        """ Save entire chassis configuration file.

        :param config_file_name: full path to the configuration file.
        """

        with open(config_file_name, 'w+') as f:
            f.write(';Chassis: {}\n'.format(self.name))
            for line in self.send_command_return_multilines('c_config', '?'):
                f.write(line.lstrip())

        for module in self.modules.values():
            module.save_config(config_file_name, 'a+')

    #
    # Properties.
    #

    @property
    def modules(self):
        """
        :return: dictionary {index: object} of all modules.
        """

        if not self.get_objects_by_type('module'):
            self.inventory()
        return {int(c.index): c for c in self.get_objects_by_type('module')}

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
        ports_str = ' '.join([p.index.replace('/', ' ') for p in ports])
        self.send_command('c_traffic', command, ports_str)
        for port in ports:
            port.wait_for_states('p_traffic', 40, command)

    def _get_operation_ports(self, *ports):
        return ports if ports else self.ports.values()


class XenaModule(XenaObject):
    """ Represents Xena module. """

    cli_prefix = 'm'

    _info_config_commands = ['m_info', 'm_config', 'm_portcount']

    def __init__(self, parent, index):
        """
        :param parent: chassis object.
        :param index: module index, 0 based.
        """

        super(self.__class__, self).__init__(objType='module', index=str(index), parent=parent)
        self.m_info = None

    def inventory(self):
        """ Get module inventory. """

        self.m_info = self.get_attributes()
        if 'NOTCFP' in self.m_info['m_cfptype']:
            a = self.get_attribute('m_portcount')
            m_portcount = int(a)
        else:
            m_portcount = int(self.get_attribute('m_cfpconfig').split()[0])
        for p_index in range(m_portcount):
            XenaPort(parent=self, index='{}/{}'.format(self.index, p_index)).inventory()

    def save_config(self, config_file_name, file_mode='w+'):
        """ Save module configuration file (including all ports under module).

        :param config_file_name: full path to the configuration file.
        :param file_mode: w+ for module configuration file, a+ for chassis configuration.
        """

        with open(config_file_name, file_mode) as f:
            f.write(';Module: {}\n'.format(self.index))
            for line in self.send_command_return_multilines('m_config', '?'):
                f.write(line.split(' ', 1)[1].lstrip())

        for port in self.ports.values():
            port.save_config(config_file_name, 'a+')

    #
    # Properties.
    #

    @property
    def ports(self):
        """
        :return: dictionary {index: object} of all ports.
        """

        if not self.get_objects_by_type('port'):
            self.inventory()
        return {int(p.index.split('/')[1]): p for p in self.get_objects_by_type('port')}
