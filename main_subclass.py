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

# Local modules
from Text2Voice.utils import text2voice
from pydub import AudioSegment
from pydub.playback import play
import os
import signal

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

def send_frame(sender, host_name, jpeg_quality, frame):
    """Encodes frame and sends it to port."""
    jpg_buffer = simplejpeg.encode_jpeg(frame, 
                quality=jpeg_quality, 
                colorspace='BGR')
    sender.send_jpg(host_name, jpg_buffer)

def kill_mode(current_stream, audio_stream):
    """Terminates current stream mode safely."""
    if current_stream:
        current_stream.terminate()
        if audio_stream:
            audio_stream.terminate()
        current_stream = None
        audio_stream = None
        time.sleep(0.006)

def choose_mode(currentKey, audios):
    """Initialize or switch desired mode as a subprocess."""
    if currentKey == "1":
        current_stream = subprocess.Popen([python_version, 'Modes/grasping.py'])
        audio_stream = subprocess.Popen([python_version, 'Modes/hand_sound.py', "--approach", "1"]) #type 1
        play(audios["grasping"])

    elif currentKey == "2":
        current_stream = subprocess.Popen([python_version, 'Modes/easy.py'],
                    bufsize=0)
        audio_stream = None
        play(audios["ocr"])

    elif currentKey == "3" or currentKey == "4" or currentKey == "5" :
        play(audios["localization"])
        if currentKey == "3":
            audio_stream = subprocess.Popen([python_version, 'Modes/3d_locate_sound.py', "--approach", "1"]) #type 1
        elif currentKey == "4":
            audio_stream = subprocess.Popen([python_version, 'Modes/3d_locate_sound.py', "--approach", "2"]) #type 2
        else:
            audio_stream = subprocess.Popen([python_version, 'Modes/3d_locate_sound.py', "--approach", "3"]) #type 3
        
        time.sleep(2)
        current_stream = subprocess.Popen([python_version, 'Modes/locate.py'],
                    bufsize=0)

        
    return current_stream,audio_stream

python_version = "python3"
# Program starts (main function)
last_key = ""
currentKey = ""

# Starts keyborad listner.
currentKey = start_key_listener(currentKey)

# Starts text to voice engine.
engine = text2voice()

# Initializing and starting multi-threaded queue webcam input stream.
# Accept connections on all tcp addresses, port 5557
sender = imagezmq.ImageSender(connect_to='tcp://127.0.0.1:5557', REQ_REP=False)
host_name = socket.gethostname() 

# Initialize webcam and allow camera sensor to warm up.
webcam = cv2.VideoCapture(0) 
time.sleep(1.0)

# Initialize current stream variable.
current_stream = None
audio_stream = None

# JPEG quality, 0 - 100 for ZMQ communication.
jpeg_quality = 95

# Audio files for modes.
audios = {"localization": AudioSegment.from_wav("./audios/localization.wav"),
            "ocr": AudioSegment.from_wav("./audios/ocr.wav"),
            "grasping":AudioSegment.from_wav("./audios/grasping.wav")}

while True:

    # Grab new frame.
    ret, frame = webcam.read()
    
    # Send frame to clients.
    send_frame(sender, host_name, jpeg_quality, frame)
    
    # Show raw frame.
    cv2.imshow("frame", frame)

    # Change current mode.
    if currentKey != last_key and currentKey in "12345":
        last_key = currentKey

        # Kill current stream mode.
        kill_mode(current_stream, audio_stream)
            
        # Initialize/switch process.
        current_stream, audio_stream = choose_mode(currentKey, audios)

    
    # Press q to end program.
    if cv2.waitKey(1) == ord("q"):
        if current_stream:
            current_stream.terminate()
            current_stream.wait()
            current_stream = None
            print("current stream finished")
            if audio_stream:
                audio_stream.terminate()
                audio_stream.kill()
                audio_stream.wait()
                audio_stream = None
                print("audio stream finished")
        break

# Close opencv windows. Check flush.
cv2.destroyAllWindows()