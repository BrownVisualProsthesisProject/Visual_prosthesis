from message_stream import MessageStreamSubscriber, MessageStreamSubscriberEvent
import json
import time
from sound_system import Sound_System
from sound_hrtf_system import Listener, load_sound, Player
import argparse
import os
import numpy as np

def scale_x(x, a, b, min_x, max_x):
    """
    Scales an integer x from the range [min_x, max_x] to the range [a, b].
    
    Parameters:
        x (int): The integer to be scaled.
        a (int): The lower bound of the target range.
        b (int): The upper bound of the target range.
        min_x (int): The lower bound of the original range.
        max_x (int): The upper bound of the original range.
    
    Returns:
        The scaled integer.
    """
    # Normalize x to the range [0, 1]
    normalized_x = (x - min_x) / (max_x - min_x)
    
    # Scale the normalized value to the target range [a, b]
    return normalized_x * (b - a) + a

def first_approach():
    hostname = 'tcp://127.0.0.1:5559'  # Use to receive from localhost
    # hostname = "192.168.86.38"  # Use to receive from other computer
    port = 5559

    imagehub = MessageStreamSubscriberEvent(hostname, port)
    # Load sound system.
    system = Sound_System()
    # Subscribes to all topics
    phi = 0
    rho = 1
    min_percentage = .15
    max_percentage = .85
    angles = np.linspace(min_percentage*180,max_percentage*180,6)
    lower_bound = angles[0]
    upper_bound = angles[1]

    while True:

        for angle in range(len(angles)-1):
            message = imagehub.recv_msg()
            
            if not message: continue

            obj = json.loads(message)
            detections = zip(obj["locs"],obj["labels"])
            detections = sorted(detections, key=lambda tup: tup[0])
    
            #could be faster y falta generar los audios
            for i in range(len(detections)):
                scaled_position = scale_x((1.0-detections[i][0])*180,angles[0],angles[-1],0,180)
                if angles[angle] <= scaled_position <= angles[angle+1]:
                    print(scaled_position)
                    if detections[i][1] == "person":
                        print(scaled_position)
                        system.play_sound("person_slow" + ".wav", rho, scaled_position, phi)
                        time.sleep(2)
                elif scaled_position > angles[angle+1]:
                    break

def second_approach():
    hostname = 'tcp://127.0.0.1:5559'  # Use to receive from localhost
    # hostname = "192.168.86.38"  # Use to receive from other computer
    port = 5559

    imagehub = MessageStreamSubscriber(hostname, port)
    min_percentage = .15
    max_percentage = .85
    angles = np.linspace(min_percentage*180,max_percentage*180,6)
    # Load sound system.
    system = Sound_System()
    # Subscribes to all topics
    phi = 0
    theta = 90
    rho = 1

    last_random = -1

    while True:


        for pos in range(len(angles)):

            system.play_sound("blip" + ".wav", rho, angles[pos], phi)
            time.sleep(2)

            if angles[pos] == angles[-1]:
                break

            message = imagehub.recv_msg()

            if not message: continue

            obj = json.loads(message)

            if obj["random"] == last_random:
                continue

            last_random = obj["random"]

            detections = zip(obj["locs"],obj["labels"])
            detections = sorted(detections, key=lambda tup: tup[0])

            #could be faster y falta generar los audios
            for i in range(len(detections)):
                scaled_position = scale_x((1.0-detections[i][0])*180,angles[0],angles[-1],0,180)
                print(scaled_position)
                if angles[pos] <= scaled_position<= angles[pos+1]:
                    print(scaled_position)
                    if detections[i][1] == "person":
                        system.play_sound("person_slow" + ".wav", rho, scaled_position, phi)
                        time.sleep(1.5)
        
        time.sleep(2.5)


def third_approach():
    hostname = 'tcp://127.0.0.1:5559'  # Use to receive from localhost
    # hostname = "192.168.86.38"  # Use to receive from other computer
    port = 5559

    imagehub = MessageStreamSubscriber(hostname, port)

    x = [0, 30, 60, 90, 120, 150, 180]

    print(os.listdir("./audios"))

    # Load sound system.
    listener = Listener()
    #initialize sound
    beep_sound = load_sound('./audios/blip.wav')
    #load sound player
    beep_player = Player()
    #set listener position
    listener.position = (180,0,0)
    listener.hrtf = 1
    #set player position
    beep_player.position = (0,0,0)
    #load sound into player
    beep_player.add(beep_sound)

    #initialize sound
    class_sound = load_sound('./audios/person_slow.wav')
    #load sound player
    class_player = Player()
    #set player position
    class_player.position = (0,0,0)
    #load sound into player
    class_player.add(class_sound)
    #enable loop sound so it plays forever
    
    # Subscribes to all topics

    last_random = -1

    while True:


        for pos in range(len(x)):
            beep_player.position = (x[pos]*2,200,0)
            beep_player.play()
            time.sleep(1.5)

            if x[pos] == x[-1]:
                break

            message = imagehub.recv_msg()

            if not message: continue

            obj = json.loads(message)

            if obj["random"] == last_random:
                continue

            last_random = obj["random"]

            detections = zip(obj["locs"],obj["labels"])
            detections = sorted(detections, key=lambda tup: tup[0])

            print(detections)
            #could be faster y falta generar los audios
            for i in range(len(detections)):
                
                if x[pos] <= detections[i][0]*180 <= x[pos+1]:
                    print(detections[i][0]*180)
                    if detections[i][1] == "person":
                        class_player.position = (detections[i][0]*180*2,200,0)
                        class_player.play()
                        time.sleep(1.5)
        
        time.sleep(2.5)
    

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--approach', type=int)
    args = parser.parse_args()

    print(args.approach, type(args.approach))
    time.sleep(5)
    if args.approach == 1:
        first_approach()
    elif  args.approach == 2:
        second_approach()
    else:
        third_approach()
    

