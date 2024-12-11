"""Hand guiding."""

# Standard modules.
import argparse
import msgpack
import time
import string
import datetime
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
import ollama
import pygame
import numpy as np
from tts import load_model
import csv

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
                    date_obj = datetime.datetime.strptime(date_str, "%m/%d/%Y")
                elif len(date_str.split('/')) == 2:  # mm/yyyy
                    date_obj = datetime.datetime.strptime(date_str, "%m/%Y")
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

import wave
def play_sentence(sentence, classifier, save_as_wav=False):
    if sentence == "":
        return 
    
    # Classify the sentence and get the NumPy array and sample rate
    npa, sample_rate = classifier(sentence)
    # Ensure the NumPy array is in the correct shape (two channels, stereo)
    #npa = np.repeat(npa.reshape(len(npa), 1), 2, axis=1)
    #npa = npa.reshape(len(npa), 1)
    
    # Play the audio using PyGame
    sound = pygame.sndarray.make_sound(npa.flatten())
    sound.play()
    pygame.time.wait(int(sound.get_length() * 1000))
    
    # Optionally, save the sound to a .wav file
    if save_as_wav:
        # Initialize PyGame mixer if needed
        pygame.mixer.init(frequency=sample_rate, size=-16, channels=2)
        
        # Generate a simple timestamp in the format YYYYMMDD_HHMMSS
        timestamp = int(time.time())
        wav_filename = f"./table/output_{timestamp}.wav"
        
        with wave.open(wav_filename, 'w') as sfile:
            # Set parameters for the wave file (sample rate, stereo, 16-bit)
            sfile.setframerate(sample_rate)
            sfile.setnchannels(2)  # Stereo
            sfile.setsampwidth(2)  # 2 bytes for 16-bit audio
            
            # Scale and convert the NumPy array to int16 for 16-bit PCM format
            # First, normalize the array if it's not already in the correct range
            max_val = np.max(np.abs(npa))  # Find the max value for normalization
            if max_val > 0:
                npa_normalized = npa / max_val  # Normalize to [-1, 1] range
            else:
                npa_normalized = npa
            
            # Convert the normalized array to int16 PCM format
            npa_int16 = (npa_normalized * 32767).astype(np.int16)
            
            # Write the audio data to the wave file
            sfile.writeframes(npa_int16.tobytes())
        
        print(f"Audio saved as {wav_filename}")


def write_to_csv(filename, sentences, phi3_response, mistral_response):
    # Open the CSV file in append mode ('a')
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        # Write the header only if the file is empty
        if file.tell() == 0:
            writer.writerow(["Prompt", "phi3 Response", "mistral-small Response"])
        # Write the sentences and the complete responses as a new row
        writer.writerow([sentences, phi3_response, mistral_response])


def format_prices(text):
    # Format prices in dollar amounts with two decimal places
    formatted_text = re.sub(r'\$\d+(\.\d{1,2})?', lambda x: f"${float(x.group()):.2f}", text)
    return formatted_text

def generate_and_process_response(model, prompt, classifier, question, vlm=False):
    print("AQUIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII")
    if vlm:
        response = ollama.chat(model=model,
                messages=[
                    {"role": "user", "content": "Describe this image ", "images": [prompt]}
                ], stream=True
            )
    else:
        response = ollama.generate(model=model, prompt=prompt, stream=True)
    complete_response = []
    current_sentence = []
    play = False
    sentence_endings = ['.', ',', '\n']  # Precompute sentence-ending characters

    # Process response tokens in chunks
    for chunk in response:
        if vlm:
            content = chunk['message']['content']
        else:
            content = chunk['response']
        current_sentence.append(content)  # Append tokens to form the sentence
        
        # Check if the current chunk ends with sentence-ending punctuation
        if any(content.endswith(punct) for punct in sentence_endings):
            sentence = replace_dates("".join(current_sentence)).strip()  # Join parts and replace dates
            #sentence = convert_prices_in_sentence(sentence)
            play_sentence(sentence, classifier, save_as_wav=play)
            complete_response.append(sentence + ("\n" if question else " "))
            current_sentence = []  # Reset for the next sentence
            print(sentence)

    return "".join(complete_response)  # Join accumulated responses


def generate_responses_for_both_models(prompt, classifier, csv_filename):
    # Generate the response using the mistral-small model
    mistral_response = generate_and_process_response('mistral-small', prompt, classifier, False)

    # Generate the response using the phi3 model
    phi3_response = generate_and_process_response('phi3', prompt, classifier, False)

    # Write the prompt, phi3 response, and mistral-small response to the CSV file
    write_to_csv(csv_filename, prompt, phi3_response, mistral_response)

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
    pygame.mixer.init(22050, -16, 1)

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
            message = imagehub.recv_msg(timeout=400.0)
            # Decode the received binary message using MessagePack
            obj = msgpack.unpackb(message)

            # Now you can access the fields as before
            raw_ocr = obj["raw_ocr"]
            closest_match = obj["close"]
            qa_flag = obj.get("qa", False)
            vlm = obj.get("vlm", False)
            
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
            if not vlm:
                prompt = "in a short sentence, what is this about: "
                prompt += raw_ocr
                # Process the response
                generate_and_process_response('mistral-small', prompt, classifier, False)
            else:
                generate_and_process_response('llava-llama3', raw_ocr, classifier, False, vlm=True)

            

            # Check if the qa flag is False, and if so, skip the user interaction part
            if not qa_flag:
                print("QA flag is not True, ending method before user interaction loop.")
                continue  # Exit the method early if qa flag is not True
            
            # After iterating over sentences, enter a loop to interact with the user until they say "no"
            while True:
                time.sleep(3)
                play_sentence("Do you have a question?", classifier)
                print("Listening for user's question...")

                if voice_mode == 1:
                    with audio_queue.mutex:
                        audio_queue.queue.clear()
                    with result_queue.mutex:
                        result_queue.queue.clear()

                    listening_event.set()
                    print("listening set")

                    try:
                        user_response = result_queue.get(timeout=30)  # Wait for up to 15 seconds
                    except queue.Empty:
                        user_response = ""

                    listening_event.clear()
                else:
                    user_response = input("Do you have a question? ")

                standardized_response = user_response.lower().strip()
                standardized_response = standardized_response.replace(".", "").replace("no", "")
                print(standardized_response)
                if standardized_response == "":
                    play_sentence("stopping language model", classifier)
                    break
                elif user_response:
                    prompt = f"in one sentence answer the question: {user_response} search the answer here: {raw_ocr}"
                    generate_and_process_response('mistral-small', prompt, classifier, True)
                else:
                    print("No response detected.")
                    break

                power_gpio()

    except KeyboardInterrupt:
        stop_flag = True
        listening_event.set()
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
