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

import pygame
import numpy as np
from tts import load_model


if platform.machine() == "aarch64":
	import Jetson.GPIO as GPIO

stop_flag = False


def find_closest_match(word):
	max_score = -1
	closest_match = None
	word_cleaned = word.translate(str.maketrans('', '', string.punctuation)).lower()
	print(word_cleaned)
	for key in LABELS:
		score = fuzz.ratio(word_cleaned, key)
		if score > .6 and score > max_score :
			max_score = score
			closest_match = key

	return closest_match

def find_closest_match(word, objects):
	max_score = -1
	closest_match = None
	word_cleaned = word.translate(str.maketrans('', '', string.punctuation)).lower()
	print(word_cleaned)
	for key in objects:
		score = fuzz.ratio(word_cleaned, key)
		if score > .6 and score > max_score :
			max_score = score
			closest_match = key

	return closest_match
	
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

def record_audio(audio_queue, energy, pause, dynamic_energy):
	#load the speech recognizer and set the initial energy threshold and pause threshold
	sr.Recognizer = CustomRecognizer
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
			audio_deque = r.listen(source)
			if not audio_deque: continue

			torch_audio = torch.cat(tuple(audio_deque), dim=0)
			#if (
			#    torch.std(torch_audio) >= 0.009
			#    and len(torch_audio) < 2.9 * 16000
			#):
			audio_queue.put_nowait(torch_audio)
			i += 1


def transcribe_forever(audio_queue, result_queue, audio_model):
	global stop_flag 
	audio_model.transcribe(torch.zeros(40000),language='english')
	
	while not stop_flag:
		audio_data = audio_queue.get()
		result = audio_model.transcribe(audio_data,language='english', fp16 = True, initial_prompt = INITIAL_PROMPT, patience=2, beam_size=10)
		result_queue.put_nowait(result["text"])


def voice_control_mode(voice_mode):
	hostname = 'tcp://127.0.0.1:5559'  # Use to receive from localhost
	# hostname = "192.168.86.38"  # Use to receive from other computer
	port = 5559

	imagehub = MessageStreamSubscriberEvent(hostname, port)
	# Load sound system.
	system = Sound_System()

	energy = .4
	pause = 0.5
	dynamic_energy = False

	# Initialize Pygame
	pygame.init()
	pygame.mixer.quit()
	pygame.mixer.init(16000, -16, 2)

	# Initialize TTS
	classifier = load_model()
	
	if voice_mode == 1:
		audio_model = whisper.load_model("tiny.en", download_root="./weights")
		audio_queue = queue.Queue()
		result_queue = queue.Queue()
		record_thread = threading.Thread(target=record_audio,
						args=(audio_queue, energy, pause, dynamic_energy))
		record_thread.start()
		transcribe_thread = threading.Thread(target=transcribe_forever,
						args=(audio_queue, result_queue, audio_model))
		time.sleep(4)
		transcribe_thread.start()
		
	if platform.machine() == "aarch64":
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(CHANNEL, GPIO.OUT)
	while True:
		message = imagehub.recv_msg(timeout=300.0)
		obj = json.loads(message)
		sentences = obj["sentences"]
		closest_match = obj["close"]
		print("sentences",sentences)
		if closest_match:
			system.say_sentence("finishing")
			time.sleep(1.5)
			global stop_flag
			stop_flag = True
			if voice_mode == 1:
				transcribe_thread.join()
				record_thread.join()
			system.close_mixer()
			if platform.machine() == "aarch64":
				GPIO.cleanup()
			break

		
		print("=====",closest_match)

		#if closest_match == 'take photo' or closest_match == "t":
			#create_dummy_file("./Modes/dummy.bin")
			#wait_until_file_not_exists("./Modes/dummy.bin")
		
		for sentence in sentences:
			# Pause for 2 seconds before speaking each sentence
			pygame.time.wait(5)
			npa, sample_rate = classifier(sentence) 
			npa = np.repeat(npa.reshape(len(npa), 1), 2, axis = 1)
			# Play the audio
			sound = pygame.sndarray.make_sound(npa)
			sound.play()
			pygame.time.wait(int(sound.get_length() * 1000))
				#speech = result_queue.get() 
				#closest_match = find_closest_match(speech, objects_list)
				
				
				#if voice_mode == 1:
				#	speech = result_queue.get() 
				#	closest_match = find_closest_match(speech, objects_list)
				#else:
				#	speech = input("next/stop/: ")

				#if speech=="stop" or speech == "s": 
				#	break
				

		power_gpio()


def power_gpio():
	if platform.machine() == "aarch64":
		GPIO.output(CHANNEL, GPIO.HIGH)
		time.sleep(.03)
		GPIO.output(CHANNEL, GPIO.LOW)

			

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("--approach", type=int)
	args = parser.parse_args()

	print(args.approach, type(args.approach))
	time.sleep(3)
	if args.approach == 1:
		voice_control_mode(1)
	elif args.approach == 2:
		voice_control_mode(0)
