"""
Classes and utilities that represents a Xena Chimera port.

:author: 
"""

import os
from collections import OrderedDict

from xenavalkyrie.xena_app import XenaBaseModule

class XenaChimeraModule(XenaBaseModule):
    def __init__(self, parent, index):
        super(XenaChimeraModule, self).__init__(parent=parent, index=index)

    # Configure the module SyncE clock source
    def set_synce_source(self, source_idx):
        self.set_attributes(m_txclocksource_new=source_idx)
