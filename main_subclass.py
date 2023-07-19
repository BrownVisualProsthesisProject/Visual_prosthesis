"""Main process."""

# Standar modules
import time
import subprocess

# Third party modules
from pynput import keyboard

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

def kill_mode(current_stream, audio_stream):
    """Terminates current stream mode safely."""
    if current_stream:
        current_stream.terminate()
        if audio_stream:
            audio_stream.terminate()
        current_stream = None
        audio_stream = None
        time.sleep(0.006)

def choose_mode(currentKey):
    """Initialize or switch desired mode as a subprocess."""
    if currentKey == "1" or currentKey == "4":
        
        if currentKey == "1":
            current_stream = subprocess.Popen([python_version, 'Modes/grasping.py'])
            audio_stream = subprocess.Popen([python_version, 'Modes/hand_sound.py', "--approach", "1"]) #type 1
        elif currentKey == "4":
            current_stream = subprocess.Popen([python_version, 'Modes/grasping.py',"--model", "yolov5m"])
            audio_stream = subprocess.Popen([python_version, 'Modes/hand_sound.py', "--approach", "2"]) #type 1

    elif currentKey == "2":
        current_stream = subprocess.Popen([python_version, 'Modes/easy.py'],
                    bufsize=0)
        audio_stream = subprocess.Popen([python_version, 'Modes/hand_sound.py', "--approach", "3"]) #type 3

    elif currentKey == "3" or currentKey == "4" or currentKey == "5" :

        if currentKey == "3":
            audio_stream = subprocess.Popen([python_version, 'Modes/3d_locate_sound.py', "--approach", "1"]) #type 1
        elif currentKey == "4":
            audio_stream = subprocess.Popen([python_version, 'Modes/3d_locate_sound.py', "--approach", "2"]) #type 2
        else:
            audio_stream = subprocess.Popen([python_version, 'Modes/3d_locate_sound.py', "--approach", "3"]) #type 3
        
        time.sleep(4)
        current_stream = subprocess.Popen([python_version, 'Modes/locate.py'],
                    bufsize=0)

        
    return current_stream,audio_stream

python_version = "python3"
# Program starts (main function)
last_key = ""
currentKey = ""

# Starts keyborad listner.
currentKey = start_key_listener(currentKey)


# Initialize current stream variable.
current_stream = None
audio_stream = None

# Audio files for modes.
#audios = {"localization": AudioSegment.from_wav("./audios/localization.wav"),
#            "ocr": AudioSegment.from_wav("./audios/ocr.wav"),
#            "grasping":AudioSegment.from_wav("./audios/grasping.wav")}

def close_streams(current_stream, audio_stream):
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
    return current_stream,audio_stream

while True:

    # Change current mode.
    if currentKey != last_key and currentKey in "12345q":

        if currentKey == "q":
            close_streams(current_stream, audio_stream)
            break
        last_key = currentKey

        # Kill current stream mode.
        kill_mode(current_stream, audio_stream)
            
        # Initialize/switch process.
        current_stream, audio_stream = choose_mode(currentKey)
