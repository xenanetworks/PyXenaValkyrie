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

    def start_emulate(self):
        """ Start emulation on port.

        """
        self.send_command('p_emulate', 'on')

    def stop_emulate(self):
        """ Stop emulation on port.

        """
        self.send_command('p_emulate', 'off')

    def enable_delay(self, fid):
        """ Stop emulation on port.

        """
        self.send_command('ped_enable[{},2]' . format(fid), 'on')

    def disable_delay(self, fid):
        """ Turn off delay / jitter on flow.

        """
        self.send_command('ped_enable[{},2]' . format(fid), 'off')

    def set_const_delay(self, fid, const_delay_ns):
        """ Stop emulation on port.

        """
        self.send_command('ped_const[{},2]' . format(fid), '{}' . format(const_delay_ns))
