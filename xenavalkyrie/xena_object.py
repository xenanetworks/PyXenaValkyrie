# -*- coding: future_annotations -*-

"""
Base classes and utilities for all Xena Manager (Xena) objects.

:author: yoram@ignissoft.com
"""
import re
import time
from collections import OrderedDict
from typing import Type, List, Optional, Dict

from trafficgenerator.tgn_utils import TgnError
from trafficgenerator.tgn_object import TgnObject, TgnObjectsDict

import xenavalkyrie.xena_app


class XenaAttributeError(TgnError):
    pass


class XenaObjectsDict(TgnObjectsDict):

    def __getitem__(self, key):
        """ Override default implementation and allow access with index as well. """
        if TgnObjectsDict.__getitem__(self, key) is not None:
            return TgnObjectsDict.__getitem__(self, key)
        else:
            for obj in self:
                if obj.index == key:
                    return OrderedDict.__getitem__(self, obj)


class XenaObject(TgnObject):
    """ Base class for all Xena objects. """

    session: Optional[xenavalkyrie.xena_app.XenaSession] = None

    def __init__(self, parent: Optional[XenaObject], **data: str) -> None:
        if parent:
            self.chassis = parent.chassis
        if 'objRef' not in data:
            data['objRef'] = f'{parent.ref}/{data["objType"]}/{data["index"].split("/")[-1]}'
        if 'name' not in data:
            data['name'] = data['index']
        super().__init__(parent, **data)

    def _create(self):
        self.api.create(self)

    def reserve(self, force: Optional[bool] = False) -> None:
        """ Reserve object.

        XenaManager-2G -> [Relinquish]/Reserve Chassis/Module/Port.

        :param force: True - take forcefully, False - fail if port is reserved by other user
        """
        reservation = self.get_attribute(self.cli_prefix + '_reservation')
        if reservation == 'RESERVED_BY_YOU':
            return
        elif reservation == 'RESERVED_BY_OTHER' and not force:
            reserved_by = self.get_attribute(self.cli_prefix + '_reservedby')
            raise TgnError(f'Resource {self} reserved by {reserved_by}')
        self.relinquish()
        self.send_command(self.cli_prefix + '_reservation', 'reserve')

    def relinquish(self):
        """ Relinquish object.

        XenaManager-2G -> Relinquish Chassis/Module/Port.
        """
        if self.get_attribute(self.cli_prefix + '_reservation') != 'RELEASED':
            self.send_command(self.cli_prefix + '_reservation relinquish')

    def release(self):
        """ Release object.

        XenaManager-2G -> Release Chassis/Module/Port.
        """
        if self.get_attribute(self.cli_prefix + '_reservation') == 'RESERVED_BY_YOU':
            self.send_command(self.cli_prefix + '_reservation release')

    def send_command(self, command, *arguments):
        """ Send command with no output.

        :param command: command to send.
        :param arguments: list of command arguments.
        """
        self.api.send_command(self, command, *arguments)

    def send_command_return(self, command, *arguments):
        """ Send command and wait for single line output. """
        return self.api.send_command_return(self, command, *arguments)

    def send_command_return_multilines(self, command, *arguments):
        """ Send command and wait for multiple lines output. """
        return self.api.send_command_return_multilines(self, command, *arguments)

    def set_attributes(self, **attributes):
        """ Sets list of attributes.

        :param attributes: dictionary of {attribute: value} to set.
        """
        try:
            self.api.set_attributes(self, **attributes)
        except Exception as e:
            if '<notwritable>' in repr(e).lower() or '<badvalue>' in repr(e).lower():
                raise XenaAttributeError(e)
            else:
                raise e

    def get_attribute(self, attribute):
        """ Returns single object attribute.

        :param attribute: requested attribute to query.
        :returns: returned value.
        :rtype: str
        """
        try:
            return self.api.get_attribute(self, attribute)
        except Exception as e:
            if '#syntax error' in repr(e).lower() or 'keyerror' in repr(e).lower():
                raise XenaAttributeError(e)
            else:
                raise e

    def get_attributes(self) -> Dict[str, str]:
        """ Returns all object's attributes. """
        return self.api.get_attributes(self)

    def wait_for_states(self, attribute, timeout=40, *states):
        for _ in range(timeout):
            if self.get_attribute(attribute).lower() in [s.lower() for s in states]:
                return
            time.sleep(1)
        raise TgnError('{} failed to reach state {}, state is {} after {} seconds'.
                       format(attribute, states, self.get_attribute(attribute), timeout))

    #
    # Implement unsupported abstract methods.
    #

    def read_stat(self, captions, stat_name):
        return dict(zip(captions, self.api.get_stats(self, stat_name)))

    def get_name(self) -> str:
        pass

    def get_children(self, *types: str) -> List[TgnObject]:
        pass

    def get_objects_from_attribute(self, attribute: str) -> List[TgnObject]:
        pass

    def get_obj_class(self, obj_type: str) -> Type[TgnObject]:
        pass

    #
    # Private methods.
    #

    def _build_index_command(self, command, *arguments):
        return ('{} {}' + len(arguments) * ' {}').format(self.index, command, *arguments)

    def _extract_return(self, command, index_command_value):
        return re.sub('{}\s*{}\s*'.format(self.index, command.upper()), '', index_command_value)

    def _get_index_len(self):
        return len(self.index.split())

    def _get_command_len(self):
        return len(self.index.split())


class XenaObject21(XenaObject):
    """ Base class for all Xena objects with index_len = 2 and command_len = 1. """

    #
    # Private methods.
    #

    def _build_index_command(self, command, *arguments):
        module, port, sid = self.index.split('/')
        return ('{}/{} {} [{}]' + len(arguments) * ' {}').format(module, port, command, sid, *arguments)

    def _extract_return(self, command, index_command_value):
        module, port, sid = self.index.split('/')
        return re.sub(rf'{module}/{port}\s*{command.upper()}\s*\[{sid}\]\s*', '', index_command_value)

    def _get_index_len(self):
        return 2

    def _get_command_len(self):
        return 1
