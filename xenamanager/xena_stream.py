
import re

from xenamanager.xena_object import XenaObject


class XenaStream(XenaObject):

    def __init__(self, location, parent):
        super(self.__class__, self).__init__(objType='stream', index=location, parent=parent)

    def build_index_command(self, command, *arguments):
        module, port, sid = self.ref.split('/')
        return ('{}/{} {} [{}]' + len(arguments) * ' {}').format(module, port, command, sid, *arguments)

    def extract_return(self, command, index_command_value):
        module, port, sid = self.ref.split('/')
        return re.sub('{}/{}\s*{}\s*\[{}\]\s*'.format(module, port, command.upper(), sid), '', index_command_value)

    def get_index_len(self):
        return 2

    def get_command_len(self):
        return 1

    def read_stats(self):
        return self.read_stat(['bps', 'pps', 'bytes', 'packets'], 'pt_stream')
