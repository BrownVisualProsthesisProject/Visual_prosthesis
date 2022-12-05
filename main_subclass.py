"""Main process."""

# Standar modules
import time
import subprocess
import socket

# Third party modules
import cv2
import imagezmq
from pynput import keyboard
import simplejpeg
import json
import os

# Local modules
from Text2Voice.utils import text2voice
from pydub import AudioSegment
from pydub.playback import play
from Modes.message_stream import MessageStreamSubscriber



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
audio_stream = None

# JPEG quality, 0 - 100
jpeg_quality = 95

#Audio modes
audios = {"localization": AudioSegment.from_wav("./audios/localization.wav"),
            "ocr": AudioSegment.from_wav("./audios/ocr.wav"),
            "grasping":AudioSegment.from_wav("./audios/grasping.wav")}



while True:

    # Grab new frame.
    ret, frame = webcam.read()
    jpg_buffer = simplejpeg.encode_jpeg(frame, 
                quality=jpeg_quality, 
                colorspace='BGR')
    sender.send_jpg(host_name, jpg_buffer)
    
    # Show raw frame.
    cv2.imshow("frame", frame)

    # Change current mode.
    if currentKey != last_key and currentKey in "1234":
        last_key = currentKey

        # Kill current stream.
        if current_stream:
            current_stream.terminate()
            if audio_stream:
                audio_stream.terminate()
            current_stream = None
            audio_stream = None
            time.sleep(0.006)
            
        # Initialize/switch process.
        if currentKey == "1":
            current_stream = subprocess.Popen(['python3.8', 'Modes/grasping.py'])
            play(audios["grasping"])

        elif currentKey == "2":
            current_stream = subprocess.Popen(['python3.8', 'Modes/ocr.py'],
                    bufsize=0)
            play(audios["ocr"])

        elif currentKey == "3" or currentKey == "4" :
            current_stream = subprocess.Popen(['python3.8', 'Modes/locate.py'],
                    bufsize=0)
            if currentKey == "3":
                audio_stream = subprocess.Popen(['python3.8', 'Modes/3d_locate_sound.py', "--approach", "1"]) #type 1
            else:
                audio_stream = subprocess.Popen(['python3.8', 'Modes/3d_locate_sound.py', "--approach", "2"]) #type 2

            play(audios["localization"])

    
    # Press q to end program.
    if cv2.waitKey(1) == ord("q"):
        if current_stream:
            current_stream.terminate()
            if audio_stream:
                audio_stream.terminate()
        break

# Close opencv windows. Check flush.
cv2.destroyAllWindows()