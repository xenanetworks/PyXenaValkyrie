
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
        self.dummymode = False

    def __del__(self):
        self.disconnect()

    def is_connected(self):
        return self.connected

    def __connect(self):
        logger.debug('Connecting {} {}...'.format(self.hostname, self.port))
        if self.dummymode:
            return True

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as msg:
            logger.error("Fail to create a socket: host %s:%d, error:%s",
                         self.hostname, self.port, msg[0])
            return False

        self.sock.settimeout(self.timeout)

        try:
            self.sock.connect((self.hostname, self.port))
        except socket.error as msg:
            logger.error("Fail to connect to host %s:%d, error:%s",
                         self.hostname, self.port, msg[0])
            return False

        return True

    def connect(self):
        if self.connected:
            logger.error("Connect() on a connected socket")
            return

        if self.__connect():
            self.connected = True

    def disconnect(self):
        logger.debug("Disconnecting")
        if not self.connected:
            return

        self.connected = False
        if not self.dummymode:
            self.sock.close()

    def sendCommand(self, cmd):
        logger.debug("sendCommand(%s)", cmd)
        if not self.connected:
            logger.error("sendCommand() on a disconnected socket")
            return -1

        if self.dummymode:
            return 0

        try:
            if not self.sock.send(bytearray(cmd + '\n', 'utf-8')):
                return -1
        except socket.error as msg:
            logger.error("Fail to send a cmd, error:%s\n", msg[0])
            self.disconnect()
            return -1

        return 0

    def readReply(self):
        if not self.connected:
            logger.error("readReply() on a disconnected socket")
            return -1

        if self.dummymode:
            return '<OK>'

        reply = self.sock.recv(1024)
        if reply.find(b'---^') != -1:
            logger.debug("Receiving a syntax error message")
            # read again the syntax error msg
            reply = self.sock.recv(1024)

        str_reply = reply.decode("utf-8")
        logger.debug('Reply message({})'.format(str_reply))
        return str_reply

    def sendQuery(self, query):
        logger.debug("sendQuery(%s)", query)
        self.sendCommand(query)
        reply = self.readReply()
        return reply

    def set_keepalives(self):
        logger.debug("Setting socket keepalive")
        if self.dummymode:
            return

        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    def set_dummymode(self, enable=True):
        logger.debug("Dummy mode was %s, request to %s", self.dummymode, enable)
        if self.dummymode is enable:
            return

        was_connected = self.is_connected()
        logger.warning("BaseSocket: enabling dummy mode")
        self.disconnect()
        if enable:
            self.dummymode = True
        else:
            self.dummymode = False

        if was_connected:
            self.connect()
