"""Hand guiding."""

# Standard modules.
import argparse
import json
import time
import string
# Local modules.
from message_stream import MessageStreamSubscriberEvent
from sound_system import Sound_System
import speech_recognition as sr
import whisper
import queue
import threading
import torch
import os
from rapidfuzz import fuzz
from Constants import LABELS, INITIAL_PROMPT, CHANNEL
from utils.custom_recognizer import CustomRecognizer
import platform
import re
import requests

import pygame
import numpy as np
from tts import load_model

if platform.machine() == "aarch64":
    import Jetson.GPIO as GPIO

# Global variables
stop_flag = False
url = "http://localhost:11434/api/generate"
listening_event = threading.Event()

def find_closest_match(word):
    max_score = -1
    closest_match = None
    word_cleaned = word.translate(str.maketrans('', '', string.punctuation)).lower()
    print(word_cleaned)
    for key in LABELS:
        score = fuzz.ratio(word_cleaned, key)
        if score > .6 and score > max_score:
            max_score = score
            closest_match = key
    return closest_match

def find_closest_match_in_objects(word, objects):
    max_score = -1
    closest_match = None
    word_cleaned = word.translate(str.maketrans('', '', string.punctuation)).lower()
    print(word_cleaned)
    for key in objects:
        score = fuzz.ratio(word_cleaned, key)
        if score > .6 and score > max_score:
            max_score = score
            closest_match = key
    return closest_match

def replace_dates(text):
    # Function to replace "mm/dd/yyyy" and "mm/yyyy" with the month word
    def replace_match(match):
        date_str = match.group(0)
        if '/' in date_str:
            try:
                if len(date_str.split('/')) == 3:  # mm/dd/yyyy
                    date_obj = datetime.strptime(date_str, "%m/%d/%Y")
                elif len(date_str.split('/')) == 2:  # mm/yyyy
                    date_obj = datetime.strptime(date_str, "%m/%Y")
                return date_obj.strftime("%B")
            except ValueError:
                return date_str  # Return the original string if there's a ValueError
        return date_str
    
    # Replace dates in both formats
    text = re.sub(r'\b\d{1,2}/\d{1,2}/\d{4}\b', replace_match, text)
    text = re.sub(r'\b\d{1,2}/\d{4}\b', replace_match, text)

    return text

def create_dummy_file(filename):
    with open(filename, 'wb') as f:
        f.seek(1)
        f.write(b'\0')

def wait_until_file_not_exists(filename, timeout=5, poll_interval=0.1):
    start_time = time.time()
    while True:
        if not os.path.exists(filename):
            return True
        if timeout is not None and time.time() - start_time >= timeout:
            return False
        time.sleep(poll_interval)

def record_audio(audio_queue, energy, pause, dynamic_energy, listening_event):
    # Load the speech recognizer and set the initial energy threshold and pause threshold
    sr.Recognizer = CustomRecognizer
    r = sr.Recognizer()
    r.energy_threshold = energy
    r.pause_threshold = pause
    r.dynamic_energy_threshold = dynamic_energy
    with sr.Microphone(sample_rate=16000) as source:
        print("Microphone initialized.")
        i = 0
        global stop_flag
        while not stop_flag:
            # Wait until 'listening_event' is set
            listening_event.wait()
            print("=========seeeet")
            if stop_flag:
                break
            try:
                # Get and save audio to wav file
                audio_deque = r.listen(source)
                print("already listened")
                if not audio_deque:
                    continue
                torch_audio = torch.cat(tuple(audio_deque), dim=0).cuda()
                audio_queue.put_nowait(torch_audio)
                i += 1
            except Exception as e:
                print(f"Error during recording: {e}")
                continue

def transcribe_forever(audio_queue, result_queue, audio_model):
    global stop_flag
    audio_model.transcribe(torch.zeros(40000,device="cuda"), language='english')
    while not stop_flag:
        try:
            print("wirint audio data to trancribe")
            audio_data = audio_queue.get()
            print("got audio data to trancribe")
            result = audio_model.transcribe(
                audio_data,
                language='english',
            )
            result_queue.put_nowait(result["text"])
        except queue.Empty:
            continue
        except Exception as e:
            print(f"Error during transcription: {e}")
            continue
def play_sentence(sentence, classifier):
    npa, sample_rate = classifier(sentence)
    npa = np.repeat(npa.reshape(len(npa), 1), 2, axis=1)
    # Play the audio
    sound = pygame.sndarray.make_sound(npa)
    sound.play()
    pygame.time.wait(int(sound.get_length() * 1000))
    pygame.time.wait(5)  # Wait for 5 seconds

def voice_control_mode(voice_mode):
    global stop_flag
    stop_flag = False
    global listening_event

    hostname = 'tcp://127.0.0.1:5559'  # Use to receive from localhost
    # hostname = "192.168.86.38"  # Use to receive from other computer
    port = 5559

    imagehub = MessageStreamSubscriberEvent(hostname, port)
    # Load sound system.
    system = Sound_System()

    energy = 0.4
    pause = 0.5
    dynamic_energy = False

    # Initialize Pygame
    pygame.init()
    pygame.mixer.quit()
    pygame.mixer.init(16000, -16, 2)

    # Initialize TTS
    classifier = load_model()

    if voice_mode == 1:
        audio_model = whisper.load_model("small.en", download_root="./weights")
        audio_queue = queue.Queue()
        result_queue = queue.Queue()
        record_thread = threading.Thread(
            target=record_audio,
            args=(audio_queue, energy, pause, dynamic_energy, listening_event)
        )
        record_thread.start()
        transcribe_thread = threading.Thread(
            target=transcribe_forever,
            args=(audio_queue, result_queue, audio_model)
        )
        time.sleep(4)
        transcribe_thread.start()

    if platform.machine() == "aarch64":
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(CHANNEL, GPIO.OUT)

    try:
        while True:
            message = imagehub.recv_msg(timeout=300.0)
            obj = json.loads(message)
            sentences = obj["sentences"]
            raw_ocr = obj["raw_ocr"]
            closest_match = obj["close"]
            print("sentences", sentences)
            if closest_match:
                system.say_sentence("finishing")
                time.sleep(1.5)
                stop_flag = True
                if voice_mode == 1:
                    record_thread.join()
                    transcribe_thread.join()
                system.close_mixer()
                if platform.machine() == "aarch64":
                    GPIO.cleanup()
                break

            print("=====", closest_match)

            # Process the sentences
            ans = replace_dates(sentences)
            response_split = re.split(r'\. |\n', ans)

            # If you want to remove any empty strings from the result
            sentences = [s.strip().replace('**', '') for s in response_split if s]
            for sentence in sentences:
                # Pause for 2 seconds before speaking each sentence
                play_sentence(sentence,classifier)

            # After iterating over sentences, enter a loop to interact with the user until they say "no"
            while True:
                play_sentence("Do you have a question?", classifier)
                print("Listening for user's question...")

                if voice_mode == 1:
                    # Clear any previous audio data
                    with audio_queue.mutex:
                        audio_queue.queue.clear()
                    with result_queue.mutex:
                        result_queue.queue.clear()

                    # Set the listening_event to start recording
                    listening_event.set()
                    print("listening set")
                    # Get the speech input from the user
                    try:
                        user_response = result_queue.get(timeout=25)  # Wait for up to 15 seconds
                    except queue.Empty:
                        user_response = ""

                    # After getting the response, clear the listening_event to stop recording
                    listening_event.clear()
                else:
                    user_response = input("Do you have a question? ")

                # Standardize the user's response
                standardized_response = user_response.lower().strip()
                standardized_response = standardized_response.replace(".", "").replace(",", "")
                #standardized_response = standardized_response.replace("!", "").replace("?", "")
                standardized_response = standardized_response.replace("no", "").strip()

                if standardized_response == "":
                    # The user said "no" (or variations of "no")
                    pass  # You can also break the loop here if desired
                    break
                elif user_response:
                    # Print the transcribed speech
                    
                    # Prepare the data for the API request
                    print("User said:", user_response)

                    # Ensure raw_ocr and ans are defined; you can adjust these variables as needed
                    sentences = f"answer this: {user_response} according to this text: {raw_ocr}"
                    print("User said:", sentences)
                    ans = ""  # Initialize 'ans' as an empty string or as per your context
                    
                    """data = {
                        "model": "mistral-small",
                        "messages": [
                            {"role": "user", "content": raw_ocr},
                            {"role": "assistant", "content": ans},
                            {"role": "user", "content": user_response}
                        ],
                        "stream": False
                    }"""

                    data = {
                    "model": "mistral-small",
                    "prompt": sentences,
                    "stream": False
                    }

                    # Send the request to the API endpoint
                    try:
                        response = requests.post(url,json=data)

                        # Get the response data
                        response_data = response.json()

                        # Process the sentences
                        ans = replace_dates(response_data['response']).replace('**', '')
                        assistant_reply = re.split(r'\. |\n', ans)
                        # Print the assistant's reply
                        print("Assistant replied:", assistant_reply)

                        # Synthesize and play the assistant's reply
                        for sentence in assistant_reply:
                            play_sentence(sentence, classifier)

                        # Update 'ans' with the assistant's reply for the next iteration
                        #ans = assistant_reply

                    except requests.exceptions.RequestException as e:
                        print(f"Request failed: {e}")
                        # Optionally, inform the user
                        system.say_sentence("Sorry, I couldn't get an answer to your question.")
                else:
                    print("No response detected.")
                    # Optionally, break the loop if no response is detected
                    break

                # Continue with any additional logic
                power_gpio()


    except KeyboardInterrupt:
        # Handle any cleanup on interrupt
        stop_flag = True
        listening_event.set()  # Unblock the threads if they are waiting
        if voice_mode == 1:
            record_thread.join()
            transcribe_thread.join()
        system.close_mixer()
        if platform.machine() == "aarch64":
            GPIO.cleanup()
        print("Program terminated by user.")

def power_gpio():
    if platform.machine() == "aarch64":
        GPIO.output(CHANNEL, GPIO.HIGH)
        time.sleep(0.03)
        GPIO.output(CHANNEL, GPIO.LOW)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--approach", type=int)
    args = parser.parse_args()

    print(args.approach, type(args.approach))
    time.sleep(3)
    if args.approach == 1:
        voice_control_mode(0)
    elif args.approach == 2:
        voice_control_mode(1)
