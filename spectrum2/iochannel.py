import asyncore
import socket
import logging


class IOChannel(asyncore.dispatcher):

    def __init__(self, host, port, callback, close_callback):
        asyncore.dispatcher.__init__(self)

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.logger = logging.getLogger(self.__class__.__name__)

        self.callback = callback
        self.close_callback = close_callback
        self.buffer = bytes()

    def send_data(self, data):
        self.buffer += data

    def handle_connect(self):
        pass

    def handle_read(self):
        data = self.recv(65536)
        self.callback(data)

    def handle_write(self):
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]

    def handle_close(self):
        self.logger.info('Connection to backend closed, terminating.')
        self.close()
        self.close_callback()

    def writable(self):
        return (len(self.buffer) > 0)

    def readable(self):
        return True
