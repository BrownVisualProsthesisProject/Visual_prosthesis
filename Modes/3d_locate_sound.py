from message_stream import MessageStreamSubscriber, MessageStreamSubscriberEvent
import json
import time
from sound_system import Sound_System
from sound_hrtf_system import Listener, load_sound, Player
import argparse
import os
import numpy as np
from pynput import keyboard
from pydub import AudioSegment
import speech_recognition as sr
import whisper
import queue
import tempfile
import os
import threading
import torch
import io
import re

def record_audio(audio_queue, energy, pause, dynamic_energy):
    #load the speech recognizer and set the initial energy threshold and pause threshold
    r = sr.Recognizer()
    r.energy_threshold = energy
    r.pause_threshold = pause
    r.dynamic_energy_threshold = dynamic_energy

    with sr.Microphone(sample_rate=16000) as source:
        print("Say something!")
        i = 0
        while True:
            #get and save audio to wav file
            audio = r.listen(source)

            torch_audio = torch.from_numpy(np.frombuffer(audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0)
            audio_data = torch_audio

            audio_queue.put_nowait(audio_data)
            i += 1


def transcribe_forever(audio_queue, result_queue, audio_model):
    while True:
        audio_data = audio_queue.get()

        result = audio_model.transcribe(audio_data,language='english')

        predicted_text = result["text"]
        result_queue.put_nowait(predicted_text)

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


def count_objects(detections, threshold):

    class_counts = {}
    for pos, label in detections:

        if label in class_counts:
            class_counts[label] += 1
        else:
            class_counts[label] = 1

    return class_counts

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
                print(detections[i][0],scaled_position)
                if angles[angle] <= scaled_position <= angles[angle+1]:
                    print(detections[i][0],scaled_position)
                    if detections[i][1] == "person":
                        print(scaled_position)
                        system.play_sound("person_slow" + ".wav", rho, scaled_position, phi)
                        time.sleep(2)
                elif (1-scaled_position) > angles[angle+1]:
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

    imagehub = MessageStreamSubscriberEvent(hostname, port)
    # Load sound system.
    system = Sound_System()

    angles = [0,45,75,105,135,180]
    times = ["two","one","twelve","eleven","ten"]

    energy = 300
    pause = 0.8
    dynamic_energy = False

    audio_model = whisper.load_model("tiny")
    audio_queue = queue.Queue()
    result_queue = queue.Queue()
    record_thread = threading.Thread(target=record_audio,
                     args=(audio_queue, energy, pause, dynamic_energy))
    
    transcribe_thread = threading.Thread(target=transcribe_forever,
                     args=(audio_queue, result_queue, audio_model))
    
    
    while True:
        record_thread.start()
        transcribe_thread.start()
        time.sleep(1)
        speech = result_queue.get() 
        speech = re.sub(r'\s+', '', speech).lower().replace(".", "")
        
        # Stop recording and transcribing audio
        print(speech)
        record_thread.join()
        transcribe_thread.join()


        if speech == "locate":
            print("localizing")
            localize(imagehub, system, angles, times)
        elif speech == "description":
            print("describing")
            describe(imagehub, system, angles, times)


def localize(imagehub, system, angles, times):
    for angle in range(len(angles)-1):
        message = imagehub.recv_msg()
            
        if not message: continue
            
        obj = json.loads(message)
        detections = zip(obj["locs"],obj["labels"])
        detections = sorted(detections, key=lambda tup: tup[0])
        class_counts = {}
            #could be faster y falta generar los audios
        for i in range(len(detections)):
            scaled_position = (1.0-detections[i][0])
                #here we init the dictionary
                
            if angles[angle] <= scaled_position*180 <= angles[angle+1]:
                    # here we count 
                print(detections[i],scaled_position*180)
                    
                if detections[i][1] in class_counts:
                    class_counts[detections[i][1]] += 1
                else:
                    class_counts[detections[i][1]] = 1

            elif scaled_position > angles[angle+1]:
                break
            
        if class_counts:
            print(class_counts)
            system.describe_position(class_counts, times[angle])
                #system.play_sound("person_slow" + ".wav", rho, scaled_position, phi)
            time.sleep(3.2)
            #here we say what we count.
            #we need a new sound system that can generate the sentence from the dictionary
            #checar tts en jetson y SR en jetson
            
def describe(imagehub, system, angles, times):

    message = imagehub.recv_msg()
        
    if message:
        
        obj = json.loads(message)
        detections = zip(obj["locs"],obj["labels"])
        detections = sorted(detections, key=lambda tup: tup[0])
        class_counts = {}
            #could be faster y falta generar los audios
        for i in range(len(detections)):
            
            if detections[i][1] in class_counts:
                class_counts[detections[i][1]] += 1
            else:
                class_counts[detections[i][1]] = 1

            
        if class_counts:
            print(class_counts)
            system.describe_scene(class_counts, times[0])
                #system.play_sound("person_slow" + ".wav", rho, scaled_position, phi)
            #here we say what we count.
            #we need a new sound system that can generate the sentence from the dictionary
            #checar tts en jetson y SR en jetson
            
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
    

