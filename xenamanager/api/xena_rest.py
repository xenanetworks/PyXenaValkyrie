"""
Base classes and utilities for all Xena Manager (Xena) objects.

:author: yoram@ignissoft.com
"""

import requests
import json
from enum import Enum

from xenamanager.api.XenaSocket import XenaCommandException


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

    def connect(self, owner):
        self.session_url = '{}/{}/'.format(self.base_url, 'session')
        self._request(RestMethod.post, self.session_url, params={'user': owner})
        self.user_url = '{}{}'.format(self.session_url, owner)

    def disconnect(self):
        self._request(RestMethod.delete, self.user_url)

    def add_chassis(self, chassis):
        """
        :param chassis: chassis object
        """

        res = self._request(RestMethod.post, self.user_url, params={'ip': chassis.ip, 'port': chassis.port})
        assert(res.status_code == 201)

    def create(self, obj):
        res = self._request(RestMethod.post, '{}{}'.format(self.session_url, obj.ref.rsplit('/', 1)[0]))
        assert(res.status_code == 201)

    def send_command(self, obj, command, *arguments):
        """ Send command with no output.

        :param obj: requested object.
        :param command: command to send.
        :param arguments: list of command arguments.
        """
        self._perform_oper('{}{}'.format(self.session_url, obj.ref), command, OperReturnType.no_output, *arguments)

    def send_command_return_multilines(self, obj, command, *arguments):
        """ Send command with no output.

        :param obj: requested object.
        :param command: command to send.
        :param arguments: list of command arguments.
        """
        return self._perform_oper('{}{}'.format(self.session_url, obj.ref), command, OperReturnType.multiline_output,
                                  *arguments).json()

    def get_attribute(self, obj, attribute):
        """ Returns single object attribute.

        :param obj: requested object.
        :param attribute: requested attribute to query.
        :returns: returned value.
        :rtype: str
        """
        return self._get_attribute('{}{}'.format(self.session_url, obj.ref), attribute)

    def get_attributes(self, obj):
        """ Get all object's attributes.

        Sends multi-parameter info/config queries and returns the result as dictionary.

        :param obj: requested object.
        :returns: dictionary of <name, value> of all attributes returned by the query.
        :rtype: dict of (str, str)
        """
        return self._get_attributes('{}{}'.format(self.session_url, obj.ref))

    def set_attributes(self, obj, **attributes):
        """ Set attributes.

        :param obj: requested object.
        :param attributes: dictionary of {attribute: value} to set
        """

        attributes_url = '{}{}/attributes'.format(self.session_url, obj.ref)
        attributes_list = [{u'name': str(name), u'value': str(value)} for name, value in attributes.items()]
        self._request(RestMethod.patch, attributes_url, headers={'Content-Type': 'application/json'},
                      data=json.dumps(attributes_list))

    #
    # Atomic operations.
    #

    def _get_children(self, object_url):
        return [c['id'] for c in self._request(RestMethod.get, object_url).json()['objects']]

    def _get_list_attribute(self, object_url, attribute):
        return self._get_attribute(object_url, attribute).split()

    def _get_attribute(self, object_url, attribute):
        return self._perform_oper(object_url, attribute, OperReturnType.line_output, '?').json()

    def _get_attributes(self, object_url):
        attributes_url = '{}/attributes'.format(object_url)
        return {a['name']: a['value'] for a in self._request(RestMethod.get, attributes_url).json()}

    def _perform_oper(self, object_url, oper, return_type, *parameters):
        operation_url = '{}/operations/{}'.format(object_url, oper)
        return self._request(RestMethod.post, operation_url,
                             json={'return_type': return_type.value, 'parameters': parameters})

    def _get_stats(self, object_url):
        statistics_url = '{}/statistics'.format(object_url)
        res = self._request(RestMethod.get, statistics_url)
        return {g['name']: {c['name']: c['value'] for c in g['counters']} for g in res.json()}

    def _request(self, method, url, **kwargs):
        self.logger.debug('method: {}, url: {}, kwargs={}'.format(method.value, url, kwargs))
        ignore = kwargs.pop('ignore', False)
        res = requests.request(method.value, url, **kwargs)
        self.logger.debug('status_code: {}'.format(res.status_code))
        if not ignore and res.status_code >= 400:
            raise XenaCommandException('status_code: {}, content: {}'.format(res.status_code, res.content))
        if res.content:
            self.logger.debug('json: {}'.format(res.json()))
        return res
