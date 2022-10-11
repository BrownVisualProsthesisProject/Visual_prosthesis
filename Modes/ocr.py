"""OCR module with Tesseract."""

# Standar modules
from multiprocessing import Process

# Third party modules
import cv2
import pytesseract


class OCR(Process):
    """OCR Model.

    Attributes:
        queue (faster_fifo.Queue):
            Webcam frames queue.
        processed_queue (faster_fifo.Queue):
            Processed frames queue.
        message_queue (multiprocessing.Queue):
            Message queue to end process.
    """

    def __init__(self, queue, processed_queue, message_queue):
        """Init function."""
        super(OCR, self).__init__()
        self.stream = queue
        self.queue = processed_queue
        self.message = message_queue
        self.custom_config = r"--oem 3 --psm 6"

    def run(self):
        """OCR run method."""
        while True:

            if not self.message.empty():
                self.message.get()
                print("ends process")
                return

            if not self.stream.empty():
                frame = self.stream.get()

                self.gray = cv2.flip(frame, 0)

                res = pytesseract.image_to_string(frame, config=self.custom_config)
                print(res)



