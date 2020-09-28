"""
Classes and utilities that represents a Xena Chimera port.

:author: 
"""

import os
from collections import OrderedDict

from xenavalkyrie.xena_port import XenaBasePort, XenaPort

class XenaChimeraPort(XenaBasePort):
    def __init__(self, parent, index):
        super(XenaChimeraPort, self).__init__(parent=parent, index=index)