"""Main process."""

# Standar modules
import time
import subprocess
import socket

# Third party modules
import cv2
import imagezmq
from pynput import keyboard

# Local modules
#from Camera.cameraZMQ import WebcamStream

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


last_key = ""
currentKey = ""

# Starts keyborad listner.
currentKey = start_key_listener(currentKey)

# Starts text to voice engine.
engine = text2voice()

# Initializing and starting multi-threaded queue webcam input stream.
# Accept connections on all tcp addresses, port 5557
sender = imagezmq.ImageSender(connect_to='tcp://127.0.0.1:5557', REQ_REP=False)

host_name = socket.gethostname() # send RPi hostname with each image
webcam = cv2.VideoCapture(0)
time.sleep(1.0)  # allow camera sensor to warm up

# Initialize current stream variable.
current_stream = None

while True:

    # Grab new frame.
    ret, frame = webcam.read()
    sender.send_image(host_name, frame)
    
    # Show raw frame.
    cv2.imshow("frame", frame)

    # Change current mode.
    if currentKey != last_key and currentKey in "123":
        last_key = currentKey

        # Kill current stream.
        if current_stream:
            current_stream.terminate()
            current_stream = None
            time.sleep(0.006)
            
        # Initialize/switch process.
        if currentKey == "1":
            current_stream = subprocess.Popen(['python', 'Modes/grasping.py'])
            engine.say("Grasping mode")

        elif currentKey == "2":
            current_stream = subprocess.Popen(['python', 'Modes/ocr.py'],
                    bufsize=0)
            engine.say("Document OCR mode")

        elif currentKey == "3":
            current_stream = subprocess.Popen(['python', 'Modes/locate.py'],
                    bufsize=0)
            engine.say("Object location mode")

        engine.runAndWait()

    # Press q to end program.
    if cv2.waitKey(1) == ord("q"):
        if current_stream:
            current_stream.terminate()
        break

# Close opencv windows. Check flush.
cv2.destroyAllWindows()
