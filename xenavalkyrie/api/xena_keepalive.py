
import threading
import time


class KeepAliveThread(threading.Thread):

    def __init__(self, logger, api, interval=10):
        threading.Thread.__init__(self)
        self.nr_sent = 0
        self.logger = logger
        self.api = api
        self.interval = interval
        self.finished = threading.Event()
        self.setDaemon(True)
        self.logger.debug("KeepAlive thread Initiated")

    def stop(self):
        self.logger.debug("KeepAlive thread stopped")
        self.finished.set()
        self.join()

    def run(self):
        while not self.finished.isSet():
            self.finished.wait(self.interval)
            if (time.time() - self.api.last_command_timestamp) >= self.interval:
                try:
                    self.api.keep_alive()
                except Exception as _:
                    pass
                self.nr_sent += 1
