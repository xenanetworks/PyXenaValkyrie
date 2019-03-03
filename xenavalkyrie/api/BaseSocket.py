
import sys
import socket
import logging

# :todo: get logger from Xena socket and manage from user level.
# Change logging level to DEBUG to get low low level logging...
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(logging.Formatter('BaseSocket - %(message)s'))
logger.addHandler(stdout_handler)


class BaseSocket:

    def __init__(self, hostname, port=22611, timeout=5):
        self.hostname = hostname
        self.port = port
        self.timeout = timeout
        self.connected = False
        self.sock = None

    def __del__(self):
        self.disconnect()

    def is_connected(self):
        return self.connected

    def __connect(self):
        logger.debug('Connecting {}:{}...'.format(self.hostname, self.port))

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.hostname, self.port))

    def connect(self):
        if self.connected:
            logger.warning("Connect() on a connected socket")
            return

        self.__connect()
        self.connected = True

    def disconnect(self):
        logger.debug("Disconnecting")
        if not self.connected:
            return

        self.connected = False
        self.sock.close()

    def sendCommand(self, cmd):
        logger.debug("sendCommand(%s)", cmd)
        if not self.connected:
            raise socket.error("sendCommand() on a disconnected socket")

        try:
            self.sock.send(bytearray(cmd + '\n', 'utf-8'))
        except socket.error as error:
            self.disconnect()
            raise socket.error("Fail to send command: {}, error: {}", cmd, error)

    def readReply(self):
        if not self.connected:
            raise socket.error("readReply() on a disconnected socket")

        try:
            reply = self.sock.recv(4096)
            while not reply.endswith('\x0a'):
                reply += self.sock.recv(4096)
            if reply.find(b'---^') != -1 or reply.find(b'^---') != -1:
                # read next line for actual message
                reply = self.sock.recv(4096)
        except Exception as error:
            self.disconnect()
            raise IOError('Fail to read response, error: {}'.format(error))

        str_reply = reply.decode("utf-8")
        logger.debug('Reply message({})'.format(str_reply))
        return str_reply

    def sendQuery(self, query):
        logger.debug('sendQuery({})'.format(query))
        self.sendCommand(query)
        reply = self.readReply()
        return reply

    def set_keepalives(self):
        logger.debug("Setting socket keepalive")
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
