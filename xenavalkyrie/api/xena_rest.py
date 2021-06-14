"""
Base classes and utilities for all Xena Manager (Xena) objects.

:author: yoram@ignissoft.com
"""

import requests
import json
import time
from enum import Enum

from xenavalkyrie.api.xena_socket import XenaCommandError
from xenavalkyrie.api.xena_keepalive import KeepAliveThread


class OperReturnType(Enum):
    no_output = 'no_output'
    line_output = 'line_output'
    multiline_output = 'multiline_output'


class RestMethod(Enum):
    get = 'GET'
    delete = 'DELETE'
    patch = 'PATCH'
    post = 'POST'


class XenaRestWrapper(object):

    def __init__(self, logger, server, port=57911):
        """ Init Xena REST API.

        :param looger: application logger.
        :param server: REST server IP.
        :param port: REST TCP port.
        """

        self.logger = logger
        self.base_url = 'http://{}:{}'.format(server, port)
        self.keepalive_thread = None
        self.last_command_timestamp = time.time()

    def connect(self, owner):
        self.session_url = '{}/{}'.format(self.base_url, 'session')
        self._request(RestMethod.post, self.session_url, params={'user': owner}, ignore=True)
        self.user_url = '{}/{}'.format(self.session_url, owner)
        self.keepalive_thread = KeepAliveThread(self.logger, self)
        self.keepalive_thread.start()

    def disconnect(self):
        self.logger.info('Disconnect from {}'.format(self.user_url))
        if self.keepalive_thread:
            self.keepalive_thread.stop()
        self._request(RestMethod.delete, self.user_url)

    def add_chassis(self, chassis):
        """
        :param chassis: chassis object
        """

        res = self._request(RestMethod.post, '{}/chassis'.format(self.user_url),
                            params={'ip': chassis.ip, 'port': chassis.port})
        assert(res.status_code in [200, 201])

    def create(self, obj):
        res = self._request(RestMethod.post, '{}/{}'.format(self.session_url, obj.ref.rsplit('/', 1)[0]))
        assert(res.status_code == 201)

    def send_command(self, obj, command, *arguments):
        """ Send command with no output.

        :param obj: requested object.
        :param command: command to send.
        :param arguments: list of command arguments.
        """

        self._send_command(obj, command, OperReturnType.no_output, *arguments)

    def send_command_return(self, obj, command, *arguments):
        """ Send command with single line output.

        :param obj: requested object.
        :param command: command to send.
        :param arguments: list of command arguments.
        :return: command output.
        """

        return self._send_command(obj, command, OperReturnType.line_output, *arguments)

    def send_command_return_multilines(self, obj, command, *arguments):
        """ Send command with no output.

        :param obj: requested object.
        :param command: command to send.
        :param arguments: list of command arguments.
        :return: list of command output lines.
        :rtype: list(str)
        """

        return self._send_command(obj, command, OperReturnType.multiline_output, *arguments)

    def _send_command(self, obj, command, return_type, *arguments):
        obj_url = '{}/{}'.format(self.session_url, obj.ref)
        self.last_command_timestamp = time.time()
        if obj.__class__.__name__ == 'XenaChassis' and command.strip()[0].isdigit():
            return self._backdoor_command(obj_url, command, return_type)
        else:
            return self._perform_command(obj_url, command, return_type, *arguments).json()

    def get_attribute(self, obj, attribute):
        """ Returns single object attribute.

        :param obj: requested object.
        :param attribute: requested attribute to query.
        :returns: returned value.
        :rtype: str
        """
        return self.get_attributes(obj)[attribute]

    def get_attributes(self, obj):
        """ Get all object's attributes.

        Sends multi-parameter info/config queries and returns the result as dictionary.

        :param obj: requested object.
        :returns: dictionary of <name, value> of all attributes returned by the query.
        :rtype: dict of (str, str)
        """
        return self._get_attributes('{}/{}'.format(self.session_url, obj.ref))

    def set_attributes(self, obj, **attributes):
        """ Set attributes.

        :param obj: requested object.
        :param attributes: dictionary of {attribute: value} to set
        """

        attributes_url = '{}/{}/attributes'.format(self.session_url, obj.ref)
        attributes_list = [{u'name': str(name), u'value': str(value)} for name, value in attributes.items()]
        self._request(RestMethod.patch, attributes_url, headers={'Content-Type': 'application/json'},
                      data=json.dumps(attributes_list))

    def get_stats(self, obj, stat_name):
        """ Send CLI command that returns list of integer counters.

        :param obj: requested object.
        :param stat_name: statistics command name.
        :return: list of counters.
        :rtype: list(int)
        """
        return [int(v) for v in self.send_command_return(obj, stat_name, '?').split()]

    def keep_alive(self):
        """ Send keep alive message. """
        self.logger.debug("Send KeepAlive message")
        self._request(RestMethod.get, self.user_url)

    #
    # Atomic operations.
    #

    def _get_children(self, object_url):
        return [c['id'] for c in self._request(RestMethod.get, object_url).json()['objects']]

    def _get_list_attribute(self, object_url, attribute):
        return self._get_attribute(object_url, attribute).split()

    def _get_attribute(self, object_url, attribute):
        return self._perform_command(object_url, attribute, OperReturnType.line_output, '?').json()

    def _get_attributes(self, object_url):
        attributes_url = '{}/attributes'.format(object_url)
        return {a['name']: a['value'] for a in self._request(RestMethod.get, attributes_url).json()}

    def _perform_command(self, object_url, command, return_type, *parameters):
        operation_url = '{}/commands/{}'.format(object_url, command)
        return self._request(RestMethod.post, operation_url,
                             json={'return_type': return_type.value, 'parameters': parameters})

    def _get_stats(self, object_url):
        statistics_url = '{}/statistics'.format(object_url)
        res = self._request(RestMethod.get, statistics_url)
        return {g['name']: {c['name']: c['value'] for c in g['counters']} for g in res.json()}

    def _backdoor_command(self, chassis_url, command, return_type):
        backdoor_url = '{}/backdoor'.format(chassis_url, command)
        return self._request(RestMethod.post, backdoor_url,
                             json={'return_type': return_type.value, 'command': command})

    def _request(self, method, url, **kwargs):
        self.logger.debug(f'method: {method.value}, url: {url}, kwargs={kwargs}')
        ignore = kwargs.pop('ignore', False)
        res = requests.request(method.value, url, **kwargs)
        self.logger.debug(f'status_code: {res.status_code}')
        if not ignore and res.status_code >= 400:
            raise XenaCommandError(f'status_code: {res.status_code}, content: {res.content}')
        if res.content:
            self.logger.debug(f'json: {res.json()}')
        return res
