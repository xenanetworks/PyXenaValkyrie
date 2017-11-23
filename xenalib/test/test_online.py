#!/usr/bin/env python

import logging
import unittest

from xenalib.api.XenaSocket import XenaSocket
from xenalib.XenaManager import XenaManager


logging.basicConfig(level=logging.INFO)


class XenaTestBase(unittest.TestCase):

    def setUp(self):
        xsocket = XenaSocket('176.22.65.114')
        xsocket.connect()
        self.xm = XenaManager(xsocket, 'yshamir')

    def test_inventory(self):
        self.xm.inventory()
