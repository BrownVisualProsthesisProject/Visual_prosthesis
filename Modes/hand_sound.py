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
from rapidfuzz import fuzz
from Constants import LABELS, INITIAL_PROMPT, CHANNEL
from custom_recognizer import CustomRecognizer
import platform

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
	
def depth_to_feet(mm):
	feet = mm / 304.8
	return round(feet, 1)

def calculate_distance(x_object, y_object, x_shape, y_shape):
	# Divide the frame into 9 sections
	section_width = x_shape // 3
	section_height = y_shape // 3

	# Determine the section in which the object is located
	section_x = (x_object*x_shape) // section_width
	section_y = (max(y_object-.15,0.0)*y_shape) // section_height
	
	print("sector x",section_x,"sector y", section_y)
	# Map the section to a movement direction
	if section_x == 0 and section_y == 0:
		direction = 'up-left'
	elif section_x == 0 and section_y == 1:
		direction = 'left'
	elif section_x == 0 and section_y == 2:
		direction = 'down-left'
	elif section_x == 1 and section_y == 0:
		direction = 'up'
	elif section_x == 1 and section_y == 1:
		direction = 'in-front-of-you'
	elif section_x == 1 and section_y == 2:
		direction = 'down'
	elif section_x == 2 and section_y == 0:
		direction = 'up-right'
	elif section_x == 2 and section_y == 1:
		direction = 'right'
	elif section_x == 2 and section_y == 2:
		direction = 'down-right'
	
	return direction

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
		result = audio_model.transcribe(audio_data,language='english', fp16 = True, initial_prompt = INITIAL_PROMPT, patience=2, beam_size=5)
		result_queue.put_nowait(result["text"])


def voice_control_mode():
	hostname = 'tcp://127.0.0.1:5559'  # Use to receive from localhost
	# hostname = "192.168.86.38"  # Use to receive from other computer
	port = 5559

	imagehub = MessageStreamSubscriberEvent(hostname, port)
	# Load sound system.
	system = Sound_System()

	angles = [0,10,25,40,55,70,85,95]
	times = ["one-thirty","one-oclock","twelve-thirty","twelve-oclock","eleven-thirty","eleven-oclock","ten-thirty"]
	inverted_times = ["ten-thirty","eleven-oclock","eleven-thirty","twelve-oclock","twelve-thirty","one-oclock", "one-thirty"]

	energy = .5
	pause = 0.5
	dynamic_energy = False

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
		speech = result_queue.get() 
		closest_match = find_closest_match(speech)
		if not closest_match: 
			continue
		if len(closest_match)>14:
			continue

		if closest_match == "close":
			system.say_sentence("finishing")
			time.sleep(1.5)
			global stop_flag
			stop_flag = True
			transcribe_thread.join()
			record_thread.join()
			system.close_mixer()
			if platform.machine() == "aarch64":
				GPIO.cleanup()
			break

		if closest_match:
			message = imagehub.recv_msg()
			obj = json.loads(message)
			print("=====",closest_match)
			if closest_match == "list":
				describe(imagehub, system, times)
				power_gpio()
			elif closest_match == "find":
				localization(imagehub, system, angles, inverted_times)
				power_gpio()
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
				power_gpio()
			else:
				system.say_sentence("Sorry-I-cant-locate-that")

def power_gpio():
	if platform.machine() == "aarch64":
		GPIO.output(CHANNEL, GPIO.HIGH)
		time.sleep(.03)
		GPIO.output(CHANNEL, GPIO.LOW)
		
def keyboard_control_mode():
	if platform.machine() == "aarch64":
		GPIO.setmode(GPIO.BOARD)
		channel = 15
		GPIO.setup(channel, GPIO.OUT)
	hostname = 'tcp://127.0.0.1:5559'  # Use to receive from localhost
	# hostname = "192.168.86.38"  # Use to receive from other computer
	port = 5559

	imagehub = MessageStreamSubscriberEvent(hostname, port)
	# Load sound system.
	system = Sound_System()

	angles = [0,10,25,40,55,70,85,95]
	times = ["one-thirty","one-oclock","twelve-thirty","twelve-oclock","eleven-thirty","eleven-oclock","ten-thirty"]
	inverted_times = ["ten-thirty","eleven-oclock","eleven-thirty","twelve-oclock","twelve-thirty","one-oclock", "one-thirty"]

	time.sleep(4)

	while True:
		closest_match = input("label/list/find: ")

		if closest_match == "mute":
			closest_match = input("label/list/find: ")

		print("=====",closest_match)

		if closest_match == "close":
			time.sleep(1.5)
			system.say_sentence("finishing")
			system.close_mixer()
			if platform.machine() == "aarch64":
				GPIO.cleanup()
			break

		if closest_match:
			message = imagehub.recv_msg()
			obj = json.loads(message)
			
			if closest_match == "list":
				describe(imagehub, system, times)
				power_gpio()
			elif closest_match == "find":
				localization(imagehub, system, angles, inverted_times)
				power_gpio()
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
				power_gpio()
			else:
				system.say_sentence("Sorry-I-cant-locate-that")

def grasp(system, grasping_memory, x_shape, y_shape):

	obj_x,label,depth,obj_y = grasping_memory
	movement = calculate_distance(obj_x, obj_y, x_shape, y_shape)
	feet = depth_to_feet(depth)
	if feet < 1.0:
		sentence = f"{LABELS[label]} {movement} at-less-than-1-foot"
	else:
		sentence = f"{LABELS[label]} {movement} at{feet}-feet"

	system.say_sentence(sentence)

	

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
				
			if angles[angle] <= scaled_position*95 <= angles[angle+1]:
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
			sentence = system.describe_pos_w_depth(class_counts, times[angle])
			power_gpio()
				#system.play_sound("person_slow" + ".wav", rho, scaled_position, phi)
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
				scaled_position = detections[i][0]
					
				if angles[angle] <= scaled_position*95 <= angles[angle+1]:
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
				sentence = system.describe_pos_w_depth(class_counts, times[angle])
				power_gpio()
				#system.play_sound("person_slow" + ".wav", rho, scaled_position, phi)
				#here we say what we count.
				#we need a new sound system that can generate the sentence from the dictionary
				#checar tts en jetson y SR en jetson
			
def describe(imagehub, system, times):

	message = imagehub.recv_msg()
		
	if message:
		
		obj = json.loads(message)
		detections = zip(obj["x_locs"],obj["labels"])
		detections = sorted(detections, key=lambda tup: tup[0])
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
			sentence = system.describe_scene(class_counts, times[0])

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("--approach", type=int)
	args = parser.parse_args()

	print(args.approach, type(args.approach))
	time.sleep(3)
	if args.approach == 1:
		voice_control_mode()
	elif args.approach == 2:
		keyboard_control_mode()
