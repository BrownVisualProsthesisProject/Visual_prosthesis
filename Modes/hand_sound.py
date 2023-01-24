from message_stream import MessageStreamSubscriber, MessageStreamSubscriberEvent
import json
import time
from sound_system import Sound_System
import argparse
import random
import numpy as np


def first_approach():

    system = Sound_System()
    # Subscribes to all topics
    phi = 0
    rho = 0

    # create a dictionary to map move values to sound file names
    move_sounds = {
        "up": "up.wav",
        "down": "down.wav",
        "left": "left.wav",
        "right": "right.wav",
        "notification": "notification.wav"
    }
    
    hostname = 'tcp://127.0.0.1:5559'  # Use to receive from localhost
    # hostname = "192.168.86.38"  # Use to receive from other computer
    port = 5559

    imagehub = MessageStreamSubscriberEvent(hostname, port)


    while True:
        

        message = imagehub.recv_msg()
        
        if not message: continue
        obj = json.loads(message)
        print(obj["move"])
        # get the sound file name based on the move value
        sound_file = move_sounds[obj["move"]]

        # play the sound
        system.play_sound(sound_file, rho, 0, phi)

        time.sleep(2)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--approach', type=int)
    args = parser.parse_args()

    print(args.approach, type(args.approach))
    time.sleep(3)
    if args.approach == 1:
        first_approach()