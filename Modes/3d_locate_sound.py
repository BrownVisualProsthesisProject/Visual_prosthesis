from message_stream import MessageStreamSubscriber, MessageStreamSubscriberEvent
import json
import time
from sound_system import Sound_System
import argparse


def first_approach():
    hostname = 'tcp://127.0.0.1:5559'  # Use to receive from localhost
    # hostname = "192.168.86.38"  # Use to receive from other computer
    port = 5559

    imagehub = MessageStreamSubscriberEvent(hostname, port)

    angles = [0, 30, 60, 90, 120, 150, 180]
    current_angle = 0
    play_position_labels = []
    # Load sound system.
    system = Sound_System()
    # Subscribes to all topics
    phi = 0
    rho = 1

    lower_bound = 0
    upper_bound = 30

    while True:

        if lower_bound >= 180:
            lower_bound = 0
            upper_bound = 30
        

        message = imagehub.recv_msg()
        
        if not message: continue

        obj = json.loads(message)
        detections = zip(obj["locs"],obj["labels"])
        detections = sorted(detections, key=lambda tup: tup[0])
 
        #could be faster y falta generar los audios
        for i in range(len(detections)):
            if lower_bound <= detections[i][0]*180 <= upper_bound:
                print(detections[i][0]*180)
                if detections[i][1] == "person":
                    system.play_sound("person_slow" + ".wav", rho, detections[i][0]*180, phi)
                    time.sleep(1.5)
            elif detections[i][0]*180 > upper_bound:
                break

        lower_bound += 30
        upper_bound += 30

def second_approach():
    hostname = 'tcp://127.0.0.1:5559'  # Use to receive from localhost
    # hostname = "192.168.86.38"  # Use to receive from other computer
    port = 5559

    imagehub = MessageStreamSubscriber(hostname, port)

    angles = [0, 30, 60, 90, 120, 150, 180]
    # Load sound system.
    system = Sound_System()
    # Subscribes to all topics
    phi = 0
    theta = 90
    rho = 1

    last_random = -1

    while True:


        for pos in range(len(angles)):

            system.play_sound("beep" + ".wav", rho, angles[pos], phi)
            time.sleep(1.5)

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

            print(detections)
            #could be faster y falta generar los audios
            for i in range(len(detections)):
                
                if angles[pos] <= detections[i][0]*180 <= angles[pos+1]:
                    print(detections[i][0]*180)
                    if detections[i][1] == "person":
                        system.play_sound("person_slow" + ".wav", rho, detections[i][0]*180, phi)
                        time.sleep(1.5)
        
        time.sleep(2.5)



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--approach', type=int)
    args = parser.parse_args()

    print(args.approach, type(args.approach))
    time.sleep(4)
    if args.approach == 1:
        first_approach()
    else:
        second_approach()
    

