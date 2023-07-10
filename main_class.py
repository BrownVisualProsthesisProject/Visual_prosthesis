"""Grasping module with Yolov5."""

# Standard modules
import json
import random
import sys
import math

from custom_recognizer import CustomRecognizer
import speech_recognition as sr
from Modes.message_stream import MessageStreamSubscriberEvent
from Modes.sound_system import Sound_System

# Third party modules
import cv2
import numpy as np
import torch
import zmq
import depthai as dai
import speech_recognition as sr
import whisper
import queue
import threading
import time
from rapidfuzz import fuzz
from Modes.Constants import INITIAL_PROMPT,LABELS
import string
import argparse

from threading import Event


stop_flag = False


def record_audio(audio_queue, energy, pause, dynamic_energy):
	#load the speech recognizer and set the initial energy threshold and pause threshold
	sr.Recognizer = CustomRecognizer
	r = sr.Recognizer()
	r.energy_threshold = energy
	r.pause_threshold = pause
	r.dynamic_energy_threshold = dynamic_energy
	time.sleep(3)
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

def calc_angle(frame, offset, HFOV):
	return math.atan(math.tan(HFOV / 2.0) * offset / (frame.shape[1] / 2.0))

def send_json(locate_socket, x_locs, y_locs, x_shape, y_shape, detected_classes, depth):
	"""Sends json data for sound system."""
	messagedata = {
			"x_locs": x_locs,
			"y_locs": y_locs,
			"labels": detected_classes,
			"random": random.randint(1, sys.maxsize),
			"depth": depth,
			"x_shape": x_shape,
			"y_shape": y_shape
		}

	obj = json.dumps(messagedata)
	locate_socket.send_string(obj)

def frame2queue(show):
	context = zmq.Context()
	locate_socket = context.socket(zmq.PUB)
	locate_socket.bind("tcp://127.0.0.1:5559")
	# Optional. If set (True), the ColorCamera is downscaled from 1080p to 720p.
	# Otherwise (False), the aligned depth is automatically upscaled to 1080p
	downscaleColor = True
	fps = 20
	# The disparity is computed at this resolution, then upscaled to RGB resolution
	monoResolution = dai.MonoCameraProperties.SensorResolution.THE_400_P

	# Create pipeline
	pipeline = dai.Pipeline()
	device = dai.Device()
	queueNames = []

	# Define sources and outputs
	camRgb = pipeline.create(dai.node.ColorCamera)
	left = pipeline.create(dai.node.MonoCamera)
	right = pipeline.create(dai.node.MonoCamera)
	stereo = pipeline.create(dai.node.StereoDepth)

	rgbOut = pipeline.create(dai.node.XLinkOut)
	depthOut = pipeline.create(dai.node.XLinkOut)

	rgbOut.setStreamName("rgb")
	queueNames.append("rgb")
	depthOut.setStreamName("depth")
	queueNames.append("depth")

	#Properties
	camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)
	camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
	camRgb.setFps(fps)
	if downscaleColor: camRgb.setIspScale(2, 3)
	# For now, RGB needs fixed focus to properly align with depth.
	# This value was used during calibration
	try:
		calibData = device.readCalibration2()
		lensPosition = calibData.getLensPosition(dai.CameraBoardSocket.RGB)
		if lensPosition:
			camRgb.initialControl.setManualFocus(lensPosition)
	except:
		raise
	left.setResolution(monoResolution)
	left.setBoardSocket(dai.CameraBoardSocket.LEFT)
	left.setFps(fps)
	right.setResolution(monoResolution)
	right.setBoardSocket(dai.CameraBoardSocket.RIGHT)
	right.setFps(fps)

	stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
	# LR-check is required for depth alignment
	#stereo.initialConfig.setMedianFilter(dai.MedianFilter.KERNEL_7x7)
	stereo.setLeftRightCheck(True)
	stereo.setSubpixel(False)
	stereo.setExtendedDisparity(True) #best 
	#stereo.setOutputSize(1248, 936)
	stereo.setDepthAlign(dai.CameraBoardSocket.RGB)

	# Linking
	camRgb.isp.link(rgbOut.input)
	left.out.link(stereo.left)
	right.out.link(stereo.right)
	stereo.depth.link(depthOut.input)

	# Load Yolov5 model.
	model = torch.hub.load(
		"ultralytics/yolov5", "yolov5s"
	)  # or yolov5n - yolov5x6, custom
	# Box color.
	bgr = (0, 255, 0)  # color of the box
	# Get labels.
	classes = model.names
	# Font config for the label.
	label_font = cv2.FONT_HERSHEY_COMPLEX

	x_shape, y_shape = (1280,720)
	HFOV = np.deg2rad(.0)

	frame_count = 0
	start_time = time.time()
	
	with device:
		global stop_flag 
		device.startPipeline(pipeline)

		frameRgb = None
		depthFrame = None

		device.setIrLaserDotProjectorBrightness(0) # in mA, 0..1200
		device.setIrFloodLightBrightness(0) # in mA, 0..1500
		#x_shape, y_shape = (1248, 936) #with set outputsize
		latestPacket = {}
		latestPacket["rgb"] = None
		latestPacket["depth"] = None
		while not stop_flag:
			# Wait for transcription to complete using the event
			frame_count += 1
			queueEvents = device.getQueueEvents(("rgb", "depth"))
			for queueName in queueEvents:
				packets = device.getOutputQueue(queueName).tryGetAll()
				if len(packets) > 0:
					latestPacket[queueName] = packets[-1]
				
			if latestPacket["rgb"]:
				frameRgb = latestPacket["rgb"].getCvFrame()
				#frameRgb = cv2.resize(frameRgb, (1248, 936))
				#cv2.imshow(rgbWindowName, frameRgb)

			if latestPacket["depth"]:
				depthFrame = latestPacket["depth"].getFrame()
				depthAux = depthFrame[depthFrame != 0]
				if not depthAux.any(): continue
				#min_depth = np.percentile(depthAux, 1)
				#max_depth = np.percentile(depthFrame, 99)
				#depthFrameColor = np.interp(depthFrame, (min_depth, max_depth), (0, 255)).astype(np.uint8)
			
			if frameRgb is not None and depthFrame is not None:
				
				results = model(frameRgb)

				# Get labels and bounding boxes coordinates.
				labels = results.xyxyn[0][:, -1].cpu().numpy()
				cord = results.xyxyn[0][:, :-1].cpu().numpy()

				x_locs = [0]*len(labels)
				y_locs = [0]*len(labels)
				detected_classes = [0]*len(labels)
				object_depth = [0]*len(labels)

				for i in range(len(labels)):
					row = cord[i]
					# If confidence score is less than 0.45 we avoid making a prediction.
					if row[4] < 0.53:
						continue

					x1 = int(row[0] * x_shape) 
					y1 = int(row[1] * y_shape)
					x2 = int(row[2] * x_shape)
					y2 = int(row[3] * y_shape)

					x = x1 + (x2 - x1) // 2
					y = y1 + (y2 - y1) // 2

					z = np.median(depthFrame[y1:y2,x1:x2])
					x_dist = x - x_shape / 2
					y_dist = y - y_shape / 2
					x_dist = z*math.tan(calc_angle(depthFrame, x_dist, HFOV))
					y_dist = z*math.tan(calc_angle(depthFrame, y_dist, HFOV))

					distance = math.sqrt(x_dist ** 2 + y_dist ** 2 + z ** 2)
					#distance = math.sqrt(x ** 2 + y ** 2 + z ** 2)
					# Plot the boxes and text.
					if show:
						cv2.rectangle(frameRgb, (x1, y1), (x2, y2), bgr, 2)
						cv2.putText(frameRgb, classes[int(labels[i])], (x1, y1), label_font, 2, bgr, 2)
						cv2.putText(frameRgb, "{:.1f} m".format(distance/1000), (x1 + 10, y1 + 20), label_font, 0.7, (0,100,255))

					x_locs[i] = x / x_shape
					y_locs[i] = y / y_shape
					detected_classes[i] = classes[int(labels[i])]
					object_depth[i] = distance
				
				messagedata = {
					"x_locs": x_locs,
					"y_locs": y_locs,
					"labels": detected_classes,
					"depth": object_depth,
					"x_shape": x_shape,
					"y_shape": y_shape
				}

				obj = json.dumps(messagedata)
				locate_socket.send_string(obj)

				if show:
					# Calculate FPS
					end_time = time.time()
					elapsed_time = end_time - start_time
					fps = frame_count / elapsed_time
					# Display FPS on the frame
					cv2.putText(frameRgb, "FPS: {:.2f}".format(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
					cv2.imshow("frame", frameRgb)

					if cv2.waitKey(1) == ord('q'):
						stop_flag = True
						break				
	cv2.destroyAllWindows()

def grasp(system, grasping_memory, x_shape, y_shape):

	obj_x,label,depth,obj_y = grasping_memory
	movement = calculate_distance(obj_x, obj_y, x_shape, y_shape)
	distance = depth_to_feet(depth)
	sentence = f"{movement} about {distance} feet"

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
	parser.add_argument("--keyboard", default=0, type=int)
	parser.add_argument("--show", default=1, type=int)
	args = parser.parse_args()

	frames_thread = threading.Thread(target=frame2queue,
					 args=(args.show,))
	frames_thread.start()

	angles = [0,45,75,105,135,180]
	times = ["two","one","twelve","eleven","ten"]

	

	if not args.keyboard:
		energy = .5
		pause = 0.5
		dynamic_energy = False
		audio_model = whisper.load_model("base.en")
		audio_queue = queue.Queue()
		result_queue = queue.Queue()
		
		transcribe_thread = threading.Thread(target=transcribe_forever,
						args=(audio_queue, result_queue, audio_model))
	
		time.sleep(2)
		transcribe_thread.start()
		record_thread = threading.Thread(target=record_audio,
						args=(audio_queue, energy, pause, dynamic_energy))
		record_thread.start()

		# Connect to device and start pipeline

	hostname = 'tcp://127.0.0.1:5559'  # Use to receive from localhost
	# hostname = "192.168.86.38"  # Use to receive from other computer
	port = 5559

	imagehub = MessageStreamSubscriberEvent(hostname, port)
	system = Sound_System()

	angles = [0,45,75,105,135,180]
	times = ["two","one","twelve","eleven","ten"]

	while True:

		if args.keyboard:
			closest_match = input("label/list/find: ")
		else:
			speech = result_queue.get()
			closest_match = find_closest_match(speech)
		if closest_match == "close":
			system.say_sentence("finishing")
			if not args.keyboard:
				frames_thread.join()
				record_thread.join()
				transcribe_thread.join()
				break
			else:
				frames_thread.join()
				break

		if not closest_match: 
			continue
		if len(closest_match)>14:
			continue

		if stop_flag:
			system.say_sentence("finishing")
			record_thread.join()
			transcribe_thread.join()
			frames_thread.join()
			break

		if closest_match:
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

		if stop_flag:
			record_thread.join()
			transcribe_thread.join()
			frames_thread.join()
			break

			
