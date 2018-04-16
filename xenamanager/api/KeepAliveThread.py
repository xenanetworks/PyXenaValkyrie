
import threading
import logging
import socket

logger = logging.getLogger(__name__)


class KeepAliveThread(threading.Thread):
    def __init__(self, basesocket, interval=10):
        threading.Thread.__init__(self)
        self.message = ''
        self.nr_sent = 0
        self.basesocket = basesocket
        self.basesocket.sendQuery(self.message)
        self.interval = interval
        self.finished = threading.Event()
        self.setDaemon(True)
        logger.debug("Initiated")

    def get_nr_sent(self):
        return self.nr_sent

    def stop(self):
        logger.debug("Stopping")
        self.finished.set()
        self.join()

    def run(self):
        while not self.finished.isSet():
            self.finished.wait(self.interval)
            logger.debug("Pinging")
            try:
                self.basesocket.sendQuery(self.message)
            except socket.error as _:
                pass
            self.nr_sent += 1
