"""Webcam class."""

# Standar modules
from threading import Thread

# Third party modules
import cv2


class WebcamStream:
    """OCR Model.

    Attributes:
        queue (faster_fifo.Queue):
            Webcam frames queue.
    """

    def __init__(self, queue, stream_id=0):
        """Init function."""
        self.stream_id = stream_id  # default is 0 for main camera
        self.queue = queue
        # opening video capture stream
        self.vcap = cv2.VideoCapture(self.stream_id)
        if self.vcap.isOpened() is False:
            print("[Exiting]: Error accessing webcam stream.")
            exit(0)
        fps_input_stream = int(self.vcap.get(5))  # hardware fps
        print(f"FPS of input stream: {fps_input_stream}")

        # reading a single frame from vcap stream for initializing
        self.grabbed, self.frame = self.vcap.read()
        if self.grabbed is False:
            print("[Exiting] No more frames to read")
            exit(0)
        # self.stopped is initialized to False
        self.stopped = True
        # thread instantiation
        self.t = Thread(target=self.update, args=())
        self.t.daemon = True  # daemon threads run in background

    def start(self):
        """Start thread."""
        self.stopped = False
        self.t.start()

    def update(self):
        """Read next available frame."""
        while self.stopped is not True:
            self.grabbed, self.frame = self.vcap.read()
            if self.grabbed is False:
                print("[Exiting] No more frames to read")
                self.stopped = True
                break
            self.queue.put(self.frame)

        self.vcap.release()

    def read(self):
        """Return lastest read frame."""
        return self.frame

    def stop(self):
        """Stop reading frames."""
        self.stopped = True
