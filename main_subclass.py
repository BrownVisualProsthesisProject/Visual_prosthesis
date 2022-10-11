"""Main process."""

# Standar modules
import multiprocessing as mp
import time
from queue import Empty

# Third party modules
import cv2
import faster_fifo_reduction
from pynput import keyboard

# Local modules
from Camera.camera import WebcamStream
from faster_fifo import Queue
from Modes.mode1_subclass import Grayscale
from Modes.mode3_subclass import Detector
from Modes.ocr import OCR

from Text2Voice.utils import text2voice


def start_key_listener(currentKey):
    """Keyboard listener."""

    def on_press(key):
        """Stores selected key."""
        try:
            global currentKey
            currentKey = key.char
            print("alphanumeric key {0} pressed".format(key.char))
        except AttributeError:
            print("special key {0} pressed".format(key))

    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    return currentKey


# created a size limited queue for communication
queue = Queue(1000 * 1000)
processed_queue = Queue(1000 * 1000)
message_queue = mp.Queue()


last_key = ""
currentKey = ""

# Starts keyborad listner.
currentKey = start_key_listener(currentKey)

# Starts text to voice engine.
engine = text2voice()

# Initializing and starting multi-threaded queue webcam input stream.
webcam_stream = WebcamStream(queue, stream_id=0)
webcam_stream.start()

# Initialize current stream variable.
current_stream = None

while webcam_stream.stopped is not True:

    if queue.empty():
        continue

    # Get new frame from webcam.
    frame = queue.get()

    # Change current mode.
    if currentKey != last_key and currentKey in "123":
        last_key = currentKey

        # Kill current stream.
        if current_stream:
            message_queue.put("Kill")
            time.sleep(0.001)
            current_stream = None

        # Initialize chosen process.
        if currentKey == "1":
            current_stream = Grayscale(queue, processed_queue, message_queue)
            engine.say("Grasping mode")

        elif currentKey == "2":
            current_stream = OCR(queue, processed_queue, message_queue)
            engine.say("Document OCR mode")

            # process 2
        elif currentKey == "3":
            current_stream = Detector(queue, processed_queue, message_queue)
            engine.say("Object location mode")

        engine.runAndWait()
        current_stream.start()

    # Show processed image.
    if not processed_queue.empty():
        cv2.imshow("processed frame", processed_queue.get())

    # Show current webcam frame.
    cv2.imshow("frame", frame)

    # Press q to end program.
    if cv2.waitKey(1) == ord("q"):
        message_queue.put("Kill")
        webcam_stream.stop()
        break

# Flush queues.
try:
    queue.get(timeout=0.1)
    processed_queue.get(timeout=0.1)
except Empty:
    print("Queue is empty")

# Close opencv windows.
cv2.destroyAllWindows()
