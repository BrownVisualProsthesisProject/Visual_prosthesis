"""Hand guiding."""

# Standard modules.
import argparse
import json
import time
import string
# Local modules.
from message_stream import MessageStreamSubscriberEvent
from sound_system import Sound_System
import matplotlib.pyplot as plt
import speech_recognition as sr
import whisper
import queue
import threading
import numpy as np
import torch
import re
import math
from fuzzywuzzy import fuzz

stop_flag = False

labels = {
"person": 0,
"bicycle": 1,
"car": 2,
"motorcycle": 3,
"airplane": 4,
"bus": 5,
"train": 6,
"truck": 7,
"boat": 8,
"traffic light": 9,
"fire hydrant": 10,
"stop sign": 11,
"parking meter": 12,
"bench": 13,
"bird": 14,
"cat": 15,
"dog": 16,
"horse": 17,
"sheep": 18,
"cow": 19,
"elephant": 20,
"bear": 21,
"zebra": 22,
"giraffe": 23,
"backpack": 24,
"umbrella": 25,
"handbag": 26,
"tie": 27,
"suitcase": 28,
"frisbee": 29,
"skis": 30,
"snowboard": 31,
"sports ball": 32,
"kite": 33,
"baseball bat": 34,
"baseball glove": 35,
"skateboard": 36,
"surfboard": 37,
"tennis racket": 38,
"bottle": 39,
"wine glass": 40,
"cup": 41,
"fork": 42,
"knife": 43,
"spoon": 44,
"bowl": 45,
"banana": 46,
"apple": 47,
"sandwich": 48,
"orange": 49,
"broccoli": 50,
"carrot": 51,
"hot dog": 52,
"pizza": 53,
"donut": 54,
"cake": 55,
"chair": 56,
"couch": 57,
"potted plant": 58,
"bed": 59,
"dining table": 60,
"toilet": 61,
"tv": 62,
"laptop": 63,
"mouse": 64,
"remote": 65,
"keyboard": 66,
"cell phone": 67,
"microwave": 68,
"oven": 69,
"toaster": 70,
"sink": 71,
"refrigerator": 72,
"book": 73,
"clock": 74,
"vase": 75,
"scissors": 76,
"teddy bear": 77,
"hair drier": 78,
"toothbrush": 79,
"localization":80,
"description":81
}

def find_closest_match(word):
    max_score = -1
    closest_match = None
    word_cleaned = word.translate(str.maketrans('', '', string.punctuation))
    print(word_cleaned)
    for key in labels:
        score = fuzz.ratio(word_cleaned, key)
        if score > max_score:
            max_score = score
            closest_match = key
    if closest_match is not None:
        return closest_match
    else:
        return None
    
def depth_to_feet(mm):
    feet = mm / 304.8
    return round(feet, 1)

def calculate_distance(x_object, y_object, x_shape, y_shape):
    # Divide the frame into 9 sections
    section_width = x_shape // 3
    section_height = y_shape // 3
    
    # Determine the section in which the object is located
    section_x = (x_object*x_shape) // section_width
    section_y = (y_object*y_shape) // section_height
    
    # Map the section to a movement direction
    if section_x == 0 and section_y == 0:
        direction = 'up left'
    elif section_x == 0 and section_y == 1:
        direction = 'left'
    elif section_x == 0 and section_y == 2:
        direction = 'down left'
    elif section_x == 1 and section_y == 0:
        direction = 'up left'
    elif section_x == 1 and section_y == 1:
        direction = 'in front of you'
    elif section_x == 1 and section_y == 2:
        direction = 'down right'
    elif section_x == 2 and section_y == 0:
        direction = 'up right'
    elif section_x == 2 and section_y == 1:
        direction = 'right'
    elif section_x == 2 and section_y == 2:
        direction = 'down right'
    
    return direction

def record_audio(audio_queue, energy, pause, dynamic_energy):
    #load the speech recognizer and set the initial energy threshold and pause threshold
    r = sr.Recognizer()
    r.energy_threshold = energy
    r.pause_threshold = pause
    r.dynamic_energy_threshold = dynamic_energy

    with sr.Microphone(sample_rate=16000) as source:
        print("Say something!")
        i = 0
        global stop_flag 
        while not stop_flag:
            #get and save audio to wav file
            r.adjust_for_ambient_noise(source, duration=.22)  
            audio = r.listen(source)
            torch_audio = torch.from_numpy(np.frombuffer(audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0)
            audio_data = torch_audio
            print("mean, ",np.mean(audio_data.numpy()),"std, ",np.std(audio_data.numpy()),len(audio_data))
            if (
                np.std(audio_data.numpy()) >= 0.009
                and len(audio_data) < 2.9 * 16000
            ):
                audio_queue.put_nowait(audio_data)
            i += 1


def transcribe_forever(audio_queue, result_queue, audio_model):
    global stop_flag 
    while not stop_flag:
        audio_data = audio_queue.get()
        result = audio_model.transcribe(audio_data,language='english')
        speech = result["text"]
        result_queue.put_nowait(speech)


def first_approach():
    hostname = 'tcp://127.0.0.1:5559'  # Use to receive from localhost
    # hostname = "192.168.86.38"  # Use to receive from other computer
    port = 5559

    imagehub = MessageStreamSubscriberEvent(hostname, port)
    # Load sound system.
    system = Sound_System()

    angles = [0,45,75,105,135,180]
    times = ["two","one","twelve","eleven","ten"]

    energy = 360
    pause = 0.5
    dynamic_energy = False

    audio_model = whisper.load_model("base")
    audio_queue = queue.Queue()
    result_queue = queue.Queue()
    record_thread = threading.Thread(target=record_audio,
                     args=(audio_queue, energy, pause, dynamic_energy))
    record_thread.start()
    transcribe_thread = threading.Thread(target=transcribe_forever,
                     args=(audio_queue, result_queue, audio_model))
    time.sleep(4)
    transcribe_thread.start()

    while True:

        speech = result_queue.get() 
        speech = re.sub(r'\s+', '', speech).lower().replace(".", "")
        print(speech)

        if speech == "close":
            system.say_sentence("finishing...")
            global stop_flag
            stop_flag = True
            transcribe_thread.join()
            record_thread.join()
            break
        if len(speech)>14 or speech == "thankyou":
            continue

        closest_match = find_closest_match(speech)
        if closest_match :
            message = imagehub.recv_msg()
            obj = json.loads(message)
            print("========",closest_match)
            if closest_match == "description":
                describe(imagehub, system, times)
            elif closest_match == "localization":
                localization(imagehub, system, angles, times)
            elif closest_match in labels and closest_match in obj["labels"]:
                message = imagehub.recv_msg()
                obj = json.loads(message)
                detections = zip(obj["x_locs"],obj["labels"], obj["depth"],obj["y_locs"])
                detections = sorted(detections, key=lambda tup: tup[2])
                
                for i in range(len(detections)):
                    if detections[i][1] == closest_match:
                        print("========",detections[i][2])
                        if detections[i][2] < 1.2*1000:
                            grasp(system, detections[i], obj["x_shape"], obj["y_shape"])
                        else:
                            localize(imagehub, system, angles, times, closest_match)
                        break
            else:
                system.say_sentence("Sorry I cant locate that")

def grasp(system, grasping_memory, x_shape, y_shape):

    obj_x,label,depth,obj_y = grasping_memory
    
    movement = calculate_distance(obj_x, obj_y, x_shape, y_shape)
    sentence = f"{movement} about {depth_to_feet(depth)} feet"

    system.say_sentence(sentence)
    time.sleep(3)

    

def localize(imagehub, system, angles, times, cls=None):

    message = imagehub.recv_msg()
    obj = json.loads(message)
    detections = zip(obj["x_locs"],obj["labels"], obj["depth"])
    detections = sorted(detections, key=lambda tup: tup[0])
    
    
    for angle in range(len(angles)-1):
        class_counts = {}
        #could be faster y falta generar los audios
        for i in range(len(detections)):
            scaled_position = (1.0-detections[i][0])
                
            if angles[angle] <= scaled_position*180 <= angles[angle+1]:
                # here we count 
                if cls and detections[i][1] != cls:
                    continue
                feet = depth_to_feet(detections[i][2])
                if detections[i][1] in class_counts:
                    
                    class_counts[detections[i][1]].append(feet)
                else:
                    class_counts[detections[i][1]] = [feet]

            elif scaled_position > angles[angle+1]:
                break
            
        if class_counts:
            print(class_counts)
            system.describe_pos_w_depth(class_counts, times[angle])
                #system.play_sound("person_slow" + ".wav", rho, scaled_position, phi)
            time.sleep(3.5)
            #here we say what we count.
            #we need a new sound system that can generate the sentence from the dictionary
            #checar tts en jetson y SR en jetson

def localization(imagehub, system, angles, times):

    
    message = imagehub.recv_msg()
    if message:
        obj = json.loads(message)
        detections = zip(obj["x_locs"],obj["labels"], obj["depth"])
        detections = sorted(detections, key=lambda tup: tup[0])
        

        for angle in range(len(angles)-1):
            class_counts = {}
            for i in range(len(detections)):
                if detections[i][1] == 0: continue
                scaled_position = (1.0-detections[i][0])
                    
                if angles[angle] <= scaled_position*180 <= angles[angle+1]:
                    # here we count 
                    feet = depth_to_feet(detections[i][2])
                    if detections[i][1] in class_counts:
                        class_counts[detections[i][1]].append(feet)
                    else:
                        class_counts[detections[i][1]] = [feet]

                elif scaled_position > angles[angle+1]:
                    break
                
            if class_counts:
                print(class_counts)
                system.describe_pos_w_depth(class_counts, times[angle])
                    #system.play_sound("person_slow" + ".wav", rho, scaled_position, phi)
                time.sleep(3.8)
                #here we say what we count.
                #we need a new sound system that can generate the sentence from the dictionary
                #checar tts en jetson y SR en jetson
            
def describe(imagehub, system, times):

    message = imagehub.recv_msg()
        
    if message:
        
        obj = json.loads(message)
        detections = zip(obj["x_locs"],obj["labels"])
        detections = sorted(detections, key=lambda tup: tup[0], reverse=True)
        class_counts = {}
            #could be faster y falta generar los audios
        for i in range(len(detections)):


            if detections[i][1] == 0: continue

            if detections[i][1] in class_counts:
                class_counts[detections[i][1]] += 1
            else:
                class_counts[detections[i][1]] = 1

            
        if class_counts:
            print(class_counts)
            system.describe_scene(class_counts, times[0])

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--approach", type=int)
    args = parser.parse_args()

    print(args.approach, type(args.approach))
    time.sleep(3)
    if args.approach == 1:
        first_approach()
