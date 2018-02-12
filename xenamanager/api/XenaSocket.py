
import threading
import socket

from xenamanager.api.BaseSocket import BaseSocket


class XenaSocket(object):
    reply_ok = '<OK>'

    def __init__(self, logger, hostname, port=22611, timeout=5):
        self.logger = logger
        logger.debug("Initializing")
        self.bsocket = BaseSocket(hostname, port, timeout)
        self.access_semaphor = threading.Semaphore(1)

    def set_dummymode(self, enable=True):
        self.logger.debug("Enabling dummymode")
        self.bsocket.set_dummymode(enable)

    def is_connected(self):
        return self.bsocket.is_connected()

    def connect(self):
        self.logger.debug("Connect()")
        self.access_semaphor.acquire()
        self.bsocket.connect()
        self.bsocket.set_keepalives()
        self.access_semaphor.release()
        if not self.is_connected():
            raise Exception("Fail to connect")
        self.logger.info("Connected")

    def disconnect(self):
        self.logger.debug("Disconnect()")
        self.access_semaphor.acquire()
        self.bsocket.disconnect()
        self.access_semaphor.release()

    def __del__(self):
        self.access_semaphor.acquire()
        self.bsocket.disconnect()
        self.access_semaphor.release()

    def sendCommand(self, cmd):
        self.logger.debug("sendCommand(%s)", cmd)
        if not self.is_connected():
            raise socket.error("sendCommand on a disconnected socket")

        self.access_semaphor.acquire()
        self.bsocket.sendCommand(cmd)
        self.access_semaphor.release()
        self.logger.debug("sendCommand(%s) returning", cmd)

    def __sendQueryReplies(self, cmd):
        # send the command followed by cmd SYNC to find out
        # when the last reply arrives.
        self.access_semaphor.acquire()
        self.bsocket.sendCommand(cmd.strip('\n'))
        self.bsocket.sendCommand('SYNC')
        replies = []
        msg = self.bsocket.readReply()
        while True:
            if '\n' in msg:
                (reply, msgleft) = msg.split('\n', 1)
                # check for syntax problems
                if reply.rfind('Syntax') != -1:
                    self.logger.warning("Multiline: syntax error")
                    self.access_semaphor.release()
                    return []

                if reply.rfind('<SYNC>') == 0:
                    self.logger.debug("Multiline EOL SYNC message")
                    self.access_semaphor.release()
                    return replies

                self.logger.debug("Multiline reply: %s", reply)
                replies.append(reply + '\n')
                msg = msgleft
            else:
                # more bytes to come
                msgnew = self.bsocket.readReply()
                msg = msgleft + msgnew

    def __sendQueryReply(self, cmd):
        self.access_semaphor.acquire()
        reply = self.bsocket.sendQuery(cmd).strip('\n')
        self.access_semaphor.release()
        return reply

    def sendQuery(self, cmd, multilines=False):
        self.logger.debug("sendQuery(%s)", cmd)
        if not self.is_connected():
            self.logger.warning("sendQuery on a disconnected socket")
            return

        if multilines:
            replies = self.__sendQueryReplies(cmd)
            self.logger.debug("sendQuery(%s) -- Begin", cmd)
            for l in replies:
                self.logger.debug("%s", l.strip())
            self.logger.debug("sendQuery(%s) -- End", cmd)
            return replies

        reply = self.__sendQueryReply(cmd)
        self.logger.debug('sendQuery(%s) reply(%s)', cmd, reply)
        if reply.startswith(('#Syntax error', '<BADPARAMETER>')):
            raise Exception('sendQuery({}) reply({})'.format(cmd, reply))
        return reply

    def sendQueryVerify(self, cmd):
        cmd = cmd.strip()
        self.logger.debug("sendQueryVerify(%s)", cmd)
        if not self.is_connected():
            raise socket.error("sendQueryVerify on a disconnected socket")

        resp = self.__sendQueryReply(cmd)
        if resp != self.reply_ok:
            raise Exception('Command {} Fail Expected {} Actual {}'.format(cmd, self.reply_ok, resp))
        self.logger.debug("SendQueryVerify(%s) Succeed", cmd)
