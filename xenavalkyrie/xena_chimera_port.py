"""
Classes and utilities that represents a Xena Chimera port.

:author: 
"""

import os
from collections import OrderedDict

from xenavalkyrie.xena_port import XenaBasePort

class XenaChimeraPort(XenaBasePort):
    def __init__(self, parent, index):
        super(XenaPort, self).__init__(parent=parent, index=index)