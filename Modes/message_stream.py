"""pub_sub_receive.py -- receive OpenCV stream using PUB SUB."""

# Standard modules
import threading

# Third-party modules
import zmq


# Helper class implementing an IO deamon thread
class MessageStreamSubscriber:

    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self._stop = False
        self._data = None
        #self._data_ready = threading.Event()
        self._thread = threading.Thread(target=self._run, args=())
        self._thread.daemon = True
        self._thread.start()

    def recv_msg(self, timeout=15.0):
        #flag = self._data_ready.wait(timeout=timeout)
        #if not flag:
        #    raise TimeoutError(
        #        "Timeout while reading from subscriber tcp://{}:{}".format(self.hostname, self.port))
        #self._data_ready.clear()
        return self._data

    def _run(self):
        # Socket to talk to server
        context = zmq.Context(1)
        socket = context.socket(zmq.SUB)
        socket.connect('tcp://127.0.0.1:5559')
        socket.subscribe("")
        
        while not self._stop:
            self._data = socket.recv_string()
            #self._data_ready.set()
        socket.close()

    def close(self):
        self._stop = True

# Helper class implementing an IO deamon thread
class MessageStreamSubscriberEvent:

    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self._stop = False
        self._data = None
        self._data_ready = threading.Event()
        self._thread = threading.Thread(target=self._run, args=())
        self._thread.daemon = True
        self._thread.start()

    def recv_msg(self, timeout=30.0):
        flag = self._data_ready.wait(timeout=timeout)
        if not flag:
            raise TimeoutError(
                "Timeout while reading from subscriber tcp://{}:{}".format(self.hostname, self.port))
        self._data_ready.clear()
        return self._data

    def _run(self):
        # Socket to talk to server
        context = zmq.Context(1)
        socket = context.socket(zmq.SUB)
        socket.connect('tcp://127.0.0.1:5559')
        socket.subscribe("")
        
        while not self._stop:
            self._data = socket.recv_string()
            self._data_ready.set()
        socket.close()

    def close(self):
        self._stop = True