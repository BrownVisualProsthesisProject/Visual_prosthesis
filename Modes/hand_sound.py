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
from rapidfuzz import fuzz
import collections
from Constants import LABELS


stop_flag = False
mute_flag = False


def find_closest_match(word):
	max_score = -1
	closest_match = None
	word_cleaned = word.translate(str.maketrans('', '', string.punctuation)).lower()
	print(word_cleaned)
	for key in LABELS:
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
	section_y = min(0,((y_object-.15)*y_shape) // section_height)
	
	print("sector x",section_x,"sector y", section_y)
	# Map the section to a movement direction
	if section_x == 0 and section_y == 0:
		direction = 'up left'
	elif section_x == 0 and section_y == 1:
		direction = 'left'
	elif section_x == 0 and section_y == 2:
		direction = 'down left'
	elif section_x == 1 and section_y == 0:
		direction = 'up'
	elif section_x == 1 and section_y == 1:
		direction = 'in front of you'
	elif section_x == 1 and section_y == 2:
		direction = 'down'
	elif section_x == 2 and section_y == 0:
		direction = 'up right'
	elif section_x == 2 and section_y == 1:
		direction = 'right'
	elif section_x == 2 and section_y == 2:
		direction = 'down right'
	
	return direction

class CustomRecognizer(sr.Recognizer):
	# Special custom changes in this method
	def __init__(self):
		super().__init__()
		self.model, self.utils = torch.hub.load(repo_or_dir='./silero-vad',
												model='silero_vad',
												force_reload=True,
												source='local',
												onnx=True)
		# source.CHUNK = 1024 / source.SAMPLERATE
		self.seconds_per_buffer = float(1024) / 16000
		self.pause_buffer_count = int(math.ceil(self.pause_threshold / self.seconds_per_buffer))  # number of buffers of non-speaking audio during a phrase, before the phrase should be considered complete
		self.phrase_buffer_count = int(math.ceil(self.phrase_threshold / self.seconds_per_buffer))-2  # minimum number of buffers of speaking audio before we consider the speaking audio a phrase
		self.non_speaking_buffer_count = int(math.ceil(self.non_speaking_duration / self.seconds_per_buffer))  # maximum number of buffers of non-speaking audio to retain before and after a phrase
		
	def listen(self, source, phrase_time_limit=2):
		"""
		Records a single phrase from ``source`` (an ``AudioSource`` instance) into an ``AudioData`` instance, which it returns.

		This is done by waiting until the audio has an energy above ``recognizer_instance.energy_threshold`` (the user has started speaking), and then recording until it encounters ``recognizer_instance.pause_threshold`` seconds of non-speaking or there is no more audio input. The ending silence is not included.

		The ``timeout`` parameter is the maximum number of seconds that this will wait for a phrase to start before giving up and throwing an ``speech_recognition.WaitTimeoutError`` exception. If ``timeout`` is ``None``, there will be no wait timeout.

		The ``phrase_time_limit`` parameter is the maximum number of seconds that this will allow a phrase to continue before stopping and returning the part of the phrase processed before the time limit was reached. The resulting audio will be the phrase cut off at the time limit. If ``phrase_timeout`` is ``None``, there will be no phrase time limit.

		The ``snowboy_configuration`` parameter allows integration with `Snowboy <https://snowboy.kitt.ai/>`__, an offline, high-accuracy, power-efficient hotword recognition engine. When used, this function will pause until Snowboy detects a hotword, after which it will unpause. This parameter should either be ``None`` to turn off Snowboy support, or a tuple of the form ``(SNOWBOY_LOCATION, LIST_OF_HOT_WORD_FILES)``, where ``SNOWBOY_LOCATION`` is the path to the Snowboy root directory, and ``LIST_OF_HOT_WORD_FILES`` is a list of paths to Snowboy hotword configuration files (`*.pmdl` or `*.umdl` format).

		This operation will always complete within ``timeout + phrase_timeout`` seconds if both are numbers, either by returning the audio data, or by raising a ``speech_recognition.WaitTimeoutError`` exception.
		"""

		
		print("pause", self.pause_buffer_count,"phrase buffer", self.phrase_buffer_count, "nonspeaking", self.non_speaking_buffer_count )
		# read audio input for phrases until there is a phrase that is long enough
		elapsed_time = 0  # number of seconds of audio read
		buffer = b""  # an empty buffer means that the stream has ended and there is no data left to read

		while True:
			frames = collections.deque()
			
			while True:
				# handle waiting too long for phrase by raising an exception
				elapsed_time += self.seconds_per_buffer
				
				buffer = source.stream.read(source.CHUNK)
				
				#tensor_buffer = torch.from_numpy(np.frombuffer(buffer, np.int16).flatten().astype(np.float32) / 32768.0)
				tensor_buffer = torch.frombuffer(buffer, dtype=torch.int16).float() / 32768.0

				frames.append(tensor_buffer)
				if len(frames) > self.non_speaking_buffer_count:  # ensure we only keep the needed amount of non-speaking buffers
					frames.popleft()

				# detect whether speaking has started on audio input
				energy = self.model(tensor_buffer, 16000).item()
				if energy > self.energy_threshold: break


			# read audio input until the phrase ends
			pause_count, phrase_count = 0, 0
			phrase_start_time = elapsed_time
			while True:
				# handle phrase being too long by cutting off the audio
				elapsed_time += self.seconds_per_buffer
				if phrase_time_limit and elapsed_time - phrase_start_time > phrase_time_limit:
					return []

				buffer = source.stream.read(source.CHUNK)
				#tensor_buffer = torch.from_numpy(np.frombuffer(buffer, np.int16).flatten().astype(np.float32) / 32768.0)
				tensor_buffer = torch.frombuffer(buffer, dtype=torch.int16).float() / 32768.0

				frames.append(tensor_buffer)
				phrase_count += 1

				# check if speaking has stopped for longer than the pause threshold on the audio input
				energy = self.model(tensor_buffer, 16000).item()

				if energy > self.energy_threshold:
					pause_count = 0
				else:
					pause_count += 1
				if pause_count > self.pause_buffer_count:  # end of the phrase
					break

			# check how long the detected phrase is, and retry listening if the phrase is too short
			phrase_count -= pause_count  # exclude the buffers for the pause before the phrase
			if phrase_count >= self.phrase_buffer_count or len(buffer) == 0: break  # phrase is long enough or we've reached the end of the stream, so stop listening

		# obtain frame data
		for i in range(pause_count - self.non_speaking_buffer_count): frames.pop()  # remove extra non-speaking frames at the end
		
		return frames

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
		global mute_flag
		while not stop_flag:
			if mute_flag:
				continue
            
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
			mute_flag = True


def transcribe_forever(audio_queue, result_queue, audio_model):
	global stop_flag 
	audio_model.transcribe(torch.zeros(40000),language='english')
	
	while not stop_flag:
		audio_data = audio_queue.get()
		result = audio_model.transcribe(audio_data,language='english')
		result_queue.put_nowait(result["text"])


def first_approach():
	hostname = 'tcp://127.0.0.1:5559'  # Use to receive from localhost
	# hostname = "192.168.86.38"  # Use to receive from other computer
	port = 5559

	imagehub = MessageStreamSubscriberEvent(hostname, port)
	# Load sound system.
	system = Sound_System()

	angles = [0,45,75,105,135,180]
	times = ["two","one","twelve","eleven","ten"]

	energy = .5
	pause = 0.5
	dynamic_energy = False

	audio_model = whisper.load_model("base.en")
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
		
		closest_match = find_closest_match(speech)
		if len(closest_match)>14:
			continue

		if closest_match == "close":
			system.say_sentence("finishing")
			global stop_flag
			stop_flag = True
			transcribe_thread.join()
			record_thread.join()
			break

		if closest_match :
			message = imagehub.recv_msg()
			obj = json.loads(message)
			print("=====",closest_match)
			if closest_match == "list":
				describe(imagehub, system, times)
			elif closest_match == "find":
				localization(imagehub, system, angles, times)
			elif closest_match in obj["labels"]:
				message = imagehub.recv_msg()
				#obj = json.loads(message)
				detections = zip(obj["x_locs"],obj["labels"], obj["depth"],obj["y_locs"])
				detections = sorted(detections, key=lambda tup: tup[2])
				
				for i in range(len(detections)):
					if detections[i][1] == closest_match:
						print("====",detections[i][2])
						if detections[i][2] < 1.2*1000:
							grasp(system, detections[i], obj["x_shape"], obj["y_shape"])
						else:
							localize(imagehub, system, angles, times, closest_match)
						break
			else:
				system.say_sentence("Sorry I cant locate that")
		
		global mute_flag
		mute_flag = False

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
				time.sleep(4)
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
