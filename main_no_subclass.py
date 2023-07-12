"""Main process."""

# Standar modules
import time
import subprocess

import argparse

def kill_mode(current_stream, audio_stream):
    """Terminates current stream mode safely."""
    if current_stream:
        current_stream.terminate()
        if audio_stream:
            audio_stream.terminate()
        current_stream = None
        audio_stream = None
        time.sleep(0.006)

python_version = "python3"
# Program starts (main function)
last_key = ""
currentKey = ""

# Initialize current stream variable.
current_stream = None
audio_stream = None

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

parser = argparse.ArgumentParser()
parser.add_argument("--keyboard", default=1, type=int)
parser.add_argument("--show", default=1, type=int)
args = parser.parse_args()

current_stream = subprocess.Popen([python_version, 'Modes/grasping.py'])
audio_stream = subprocess.Popen([python_version, 'Modes/hand_sound.py', "--approach", f"{args.keyboard}"]) #type 1 or 2

while True:

    closest_match = input("q: ")
    if closest_match == "q":
        close_streams(current_stream,audio_stream)
        break
