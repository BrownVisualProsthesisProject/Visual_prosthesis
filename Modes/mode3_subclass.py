"""Localization module with Yolov5."""

# Standar modules
from multiprocessing import Process

# Third party modules
import cv2 

class Detector(Process):
    """Object Localization Model.

    Attributes:
        queue (faster_fifo.Queue):
            Webcam frames queue.
        processed_queue (faster_fifo.Queue):
            Processed frames queue.
        message_queue (multiprocessing.Queue):
            Message queue to end process.
    """

    def __init__(self, queue, processed_queue, message_queue):
        """init function."""
        super(Detector, self).__init__()
        self.stream = queue
        self.queue = processed_queue
        self.message = message_queue

    def run(self):
        """Localization run method."""
        while True :

            if not self.message.empty():
                self.message.get()
                print("ends process")
                return

            if not self.stream.empty():
                frame = self.stream.get()
                self.gray = cv2.Canny(frame, 30, 150)
                self.queue.put(self.gray)
