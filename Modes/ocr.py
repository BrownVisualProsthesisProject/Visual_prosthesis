"""Grasping module with Yolov5."""

# Standard modules
import json

# Third party modules
import argparse
import cv2
import numpy as np
import torch
import zmq
import depthai as dai
import time 
import os

import pygame
import cv2
from easyocr import Reader
import numpy as np
from tts import load_model
from ocr_utils.rectangle import BoundingBox

colors = [
	(255, 0, 0),    # Red
	(0, 255, 0),    # Green
	(0, 0, 255),    # Blue
	(255, 255, 0),  # Yellow
	(255, 0, 255),  # Magenta
	(0, 255, 255),  # Cyan
	(128, 0, 0),    # Maroon
	(0, 128, 0),    # Green (lime)
	(0, 0, 128),    # Navy
	(128, 128, 0),  # Olive
	(128, 0, 128),  # Purple
	(0, 128, 128),  # Teal
	(192, 192, 192),# Silver
	(128, 128, 128),# Gray
	(255, 165, 0),  # Orange
	(255, 255, 255),# White
	(0, 0, 0),      # Black
	(255, 255, 128),# Light Yellow
	(128, 128, 255),# Light Blue
	(255, 128, 128),# Light Red
	(128, 255, 128),# Light Green
	(128, 255, 255),# Light Cyan
	(255, 128, 255),# Light Magenta
	(128, 0, 64),   # Dark Red
	(0, 128, 64),   # Dark Green
	(0, 64, 128),   # Dark Blue
	(128, 64, 0),   # Dark Yellow
	(64, 0, 128),   # Dark Magenta
	(64, 128, 0),   # Dark Cyan
	(64, 64, 64),    # Dark Gray
	(255, 0, 0),    # Red
	(0, 255, 0),    # Green
	(0, 0, 255),    # Blue
	(255, 255, 0),  # Yellow
	(255, 0, 255),  # Magenta
	(0, 255, 255),  # Cyan
	(128, 0, 0),    # Maroon
	(0, 128, 0),    # Green (lime)
	(0, 0, 128),    # Navy
	(128, 128, 0),  # Olive
	(128, 0, 128),  # Purple
	(0, 128, 128),  # Teal
	(192, 192, 192),# Silver
	(128, 128, 128),# Gray
	(255, 165, 0),  # Orange
	(255, 255, 255),# White
	(0, 0, 0),      # Black
	(255, 255, 128),# Light Yellow
	(128, 128, 255),# Light Blue
	(255, 128, 128),# Light Red
	(128, 255, 128),# Light Green
	(128, 255, 255),# Light Cyan
	(255, 128, 255),# Light Magenta
	(128, 0, 64),   # Dark Red
	(0, 128, 64),   # Dark Green
	(0, 64, 128),   # Dark Blue
	(128, 64, 0),   # Dark Yellow
	(64, 0, 128),   # Dark Magenta
	(64, 128, 0),   # Dark Cyan
	(64, 64, 64),    # Dark Gray
	(255, 0, 0),    # Red
	(0, 255, 0),    # Green
	(0, 0, 255),    # Blue
	(255, 255, 0),  # Yellow
	(255, 0, 255),  # Magenta
	(0, 255, 255),  # Cyan
	(128, 0, 0),    # Maroon
	(0, 128, 0),    # Green (lime)
	(0, 0, 128),    # Navy
	(128, 128, 0),  # Olive
	(128, 0, 128),  # Purple
	(0, 128, 128),  # Teal
	(192, 192, 192),# Silver
	(128, 128, 128),# Gray
	(255, 165, 0),  # Orange
	(255, 255, 255),# White
	(0, 0, 0),      # Black
	(255, 255, 128),# Light Yellow
	(128, 128, 255),# Light Blue
	(255, 128, 128),# Light Red
	(128, 255, 128),# Light Green
	(128, 255, 255),# Light Cyan
	(255, 128, 255),# Light Magenta
	(128, 0, 64),   # Dark Red
	(0, 128, 64),   # Dark Green
	(0, 64, 128),   # Dark Blue
	(128, 64, 0),   # Dark Yellow
	(64, 0, 128),   # Dark Magenta
	(64, 128, 0),   # Dark Cyan
	(64, 64, 64),    # Dark Gray
	(255, 0, 0),    # Red
	(0, 255, 0),    # Green
	(0, 0, 255),    # Blue
	(255, 255, 0),  # Yellow
	(255, 0, 255),  # Magenta
	(0, 255, 255),  # Cyan
	(128, 0, 0),    # Maroon
	(0, 128, 0),    # Green (lime)
	(0, 0, 128),    # Navy
	(128, 128, 0),  # Olive
	(128, 0, 128),  # Purple
	(0, 128, 128),  # Teal
	(192, 192, 192),# Silver
	(128, 128, 128),# Gray
	(255, 165, 0),  # Orange
	(255, 255, 255),# White
	(0, 0, 0),      # Black
	(255, 255, 128),# Light Yellow
	(128, 128, 255),# Light Blue
	(255, 128, 128),# Light Red
	(128, 255, 128),# Light Green
	(128, 255, 255),# Light Cyan
	(255, 128, 255),# Light Magenta
	(128, 0, 64),   # Dark Red
	(0, 128, 64),   # Dark Green
	(0, 64, 128),   # Dark Blue
	(128, 64, 0),   # Dark Yellow
	(64, 0, 128),   # Dark Magenta
	(64, 128, 0),   # Dark Cyan
	(64, 64, 64),    # Dark Gray
	(255, 0, 0),    # Red
	(0, 255, 0),    # Green
	(0, 0, 255),    # Blue
	(255, 255, 0),  # Yellow
	(255, 0, 255),  # Magenta
	(0, 255, 255),  # Cyan
	(128, 0, 0),    # Maroon
	(0, 128, 0),    # Green (lime)
	(0, 0, 128),    # Navy
	(128, 128, 0),  # Olive
	(128, 0, 128),  # Purple
	(0, 128, 128),  # Teal
	(192, 192, 192),# Silver
	(128, 128, 128),# Gray
	(255, 165, 0),  # Orange
	(255, 255, 255),# White
	(0, 0, 0),      # Black
	(255, 255, 128),# Light Yellow
	(128, 128, 255),# Light Blue
	(255, 128, 128),# Light Red
	(128, 255, 128),# Light Green
	(128, 255, 255),# Light Cyan
	(255, 128, 255),# Light Magenta
	(128, 0, 64),   # Dark Red
	(0, 128, 64),   # Dark Green
	(0, 64, 128),   # Dark Blue
	(128, 64, 0),   # Dark Yellow
	(64, 0, 128),   # Dark Magenta
	(64, 128, 0),   # Dark Cyan
	(64, 64, 64),    # Dark Gray
	(255, 0, 0),    # Red
	(0, 255, 0),    # Green
	(0, 0, 255),    # Blue
	(255, 255, 0),  # Yellow
	(255, 0, 255),  # Magenta
	(0, 255, 255),  # Cyan
	(128, 0, 0),    # Maroon
	(0, 128, 0),    # Green (lime)
	(0, 0, 128),    # Navy
	(128, 128, 0),  # Olive
	(128, 0, 128),  # Purple
	(0, 128, 128),  # Teal
	(192, 192, 192),# Silver
	(128, 128, 128),# Gray
	(255, 165, 0),  # Orange
	(255, 255, 255),# White
	(0, 0, 0),      # Black
	(255, 255, 128),# Light Yellow
	(128, 128, 255),# Light Blue
	(255, 128, 128),# Light Red
	(128, 255, 128),# Light Green
	(128, 255, 255),# Light Cyan
	(255, 128, 255),# Light Magenta
	(128, 0, 64),   # Dark Red
	(0, 128, 64),   # Dark Green
	(0, 64, 128),   # Dark Blue
	(128, 64, 0),   # Dark Yellow
	(64, 0, 128),   # Dark Magenta
	(64, 128, 0),   # Dark Cyan
	(64, 64, 64),    # Dark Gray
	(255, 0, 0),    # Red
	(0, 255, 0),    # Green
	(0, 0, 255),    # Blue
	(255, 255, 0),  # Yellow
	(255, 0, 255),  # Magenta
	(0, 255, 255),  # Cyan
	(128, 0, 0),    # Maroon
	(0, 128, 0),    # Green (lime)
	(0, 0, 128),    # Navy
	(128, 128, 0),  # Olive
	(128, 0, 128),  # Purple
	(0, 128, 128),  # Teal
	(192, 192, 192),# Silver
	(128, 128, 128),# Gray
	(255, 165, 0),  # Orange
	(255, 255, 255),# White
	(0, 0, 0),      # Black
	(255, 255, 128),# Light Yellow
	(128, 128, 255),# Light Blue
	(255, 128, 128),# Light Red
	(128, 255, 128),# Light Green
	(128, 255, 255),# Light Cyan
	(255, 128, 255),# Light Magenta
	(128, 0, 64),   # Dark Red
	(0, 128, 64),   # Dark Green
	(0, 64, 128),   # Dark Blue
	(128, 64, 0),   # Dark Yellow
	(64, 0, 128),   # Dark Magenta
	(64, 128, 0),   # Dark Cyan
	(64, 64, 64),    # Dark Gray
	(255, 0, 0),    # Red
	(0, 255, 0),    # Green
	(0, 0, 255),    # Blue
	(255, 255, 0),  # Yellow
	(255, 0, 255),  # Magenta
	(0, 255, 255),  # Cyan
	(128, 0, 0),    # Maroon
	(0, 128, 0),    # Green (lime)
	(0, 0, 128),    # Navy
	(128, 128, 0),  # Olive
	(128, 0, 128),  # Purple
	(0, 128, 128),  # Teal
	(192, 192, 192),# Silver
	(128, 128, 128),# Gray
	(255, 165, 0),  # Orange
	(255, 255, 255),# White
	(0, 0, 0),      # Black
	(255, 255, 128),# Light Yellow
	(128, 128, 255),# Light Blue
	(255, 128, 128),# Light Red
	(128, 255, 128),# Light Green
	(128, 255, 255),# Light Cyan
	(255, 128, 255),# Light Magenta
	(128, 0, 64),   # Dark Red
	(0, 128, 64),   # Dark Green
	(0, 64, 128),   # Dark Blue
	(128, 64, 0),   # Dark Yellow
	(64, 0, 128),   # Dark Magenta
	(64, 128, 0),   # Dark Cyan
	(64, 64, 64),    # Dark Gray
]

def is_half_numbers(sentence):
	total_chars = len(sentence)
	num_chars = sum(1 for char in sentence if char.isdigit())
	return num_chars / total_chars >= 0.5

def compare(x, y):
	return 1 if x + y < y + x else -1
	
class UnionFind:
	def __init__(self):
		self.parent = {}

	def find(self, x):
		if x not in self.parent:
			self.parent[x] = x
			return x
		elif self.parent[x] == x:
			return x
		else:
			self.parent[x] = self.find(self.parent[x])
			return self.parent[x]

	def union(self, x, y):
		root_x = self.find(x)
		root_y = self.find(y)
		if root_x != root_y:
			self.parent[root_x] = root_y


def overlapping(bbox1, bbox2):
	# Check if two bounding boxes overlap
	x_overlap = not (bbox1.br[0] < bbox2.tl[0] or bbox2.br[0] < bbox1.tl[0])
	y_overlap = not (bbox1.br[1] < bbox2.tl[1] or bbox2.br[1] < bbox1.tl[1])
	return x_overlap and y_overlap


def group_overlapping_bboxes(bboxes):
	uf = UnionFind()

	# Initialize groups
	for i, bbox1 in enumerate(bboxes):
		for j, bbox2 in enumerate(bboxes[i+1:]):
			if overlapping(bbox1, bbox2):
				uf.union(i, i+j+1)

	# Create groups
	groups = {}
	for i, bbox in enumerate(bboxes):
		root = uf.find(i)
		if root not in groups:
			groups[root] = []
		groups[root].append(bbox)

	return groups


def send_json(locate_socket, sentences):
	"""Sends json data for sound system."""
	messagedata = {
			"sentences": sentences,
		}

	obj = json.dumps(messagedata)
	locate_socket.send_string(obj)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--model", default="yolov5m_Objects365", type=str)
	parser.add_argument("--distort", default=0, type=str)
	args = parser.parse_args()
	context = zmq.Context()
	locate_socket = context.socket(zmq.PUB)
	locate_socket.bind("tcp://127.0.0.1:5559")

	# Optional. If set (True), the ColorCamera is downscaled from 1080p to 720p.
	# Otherwise (False), the aligned depth is automatically upscaled to 1080p
	downscaleColor = False
	fps = 12
	# The disparity is computed at this resolution, then upscaled to RGB resolution
	rgbResolution = dai.ColorCameraProperties.SensorResolution.THE_1080_P

	# Create pipeline
	pipeline = dai.Pipeline()
	
	queueNames = []

	# Define source and output
	camRgb = pipeline.create(dai.node.ColorCamera)
	camRgb.setFps(30)
	camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_12_MP)

	controlIn = pipeline.create(dai.node.XLinkIn)
	controlIn.setStreamName('control')
	controlIn.out.link(camRgb.inputControl)

	xout = pipeline.create(dai.node.XLinkOut)
	xout.setStreamName("out")
	camRgb.isp.link(xout.input)
	camRgb.setIspScale(1,2)

	counter = 0
	# Initialize Pygame
	pygame.init()
	pygame.mixer.quit()
	pygame.mixer.init(16000, -16, 2)

	# Initialize EasyOCR reader
	reader = Reader(['en'], recog_network="english_g2")
	# Initialize TTS
	classifier = load_model()

		# Connect to device and start pipeline
	with dai.Device(pipeline) as device:
		q = device.getOutputQueue(name="out")

		#HFOV = np.deg2rad(90.0)
		frame_count = 0
		start_time = time.time()

		while True:
			frameRgb = q.get().getCvFrame()

			if os.path.exists("./Modes/dummy.bin"):
				results_top = reader.readtext(frameRgb, width_ths=5, text_threshold=.7)
				# Combine the text of the bounding boxes to create one paragraph
				combined_text = ""
				for (bbox, text, prob) in results_top:
					combined_text += text + " "

				#sentences = sent_tokenize(combined_text)
				#bboxess = results_top
				#print("----", bboxess)
				#bboxess_sorted = sorted(bboxess, key=lambda x: (x[0][0][1], x[0][0][0]))
				#print("----", bboxess_sorted)
						

				# Draw bounding boxes around the detected text
				for (bbox, text, prob) in results_top:
					# Extract bounding box coordinates
					(tl, tr, br, bl) = bbox
					tl = (int(tl[0]), int(tl[1]))
					tr = (int(tr[0]), int(tr[1]))
					br = (int(br[0]), int(br[1]))
					bl = (int(bl[0]), int(bl[1]))

				
				# Group overlapping bounding boxes
				bbox_groups = group_overlapping_bboxes([BoundingBox(bbox, text, prob) for bbox, text, prob in results_top])
				counter = -1
				# Draw bounding box
				for group in bbox_groups:
					bbox_groups[group] = sorted(bbox_groups[group])
					for bbox in bbox_groups[group]:
						tl = bbox.tl
						br = bbox.br
						text_x = int((tl[0] + br[0]) / 2) - 10  # Adjusting for text width
						text_y = int((tl[1] + br[1]) / 2) + 10  # Adjusting for text height
						# Calculate width and height of the bounding box
						width = bbox.width
						height = bbox.height
						# Add text indicating the order of the rectangle along with width and height
						counter += 1
						cv2.putText(frameRgb, f"{counter}", (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
						cv2.rectangle(frameRgb, tl, br, colors[group], 2)

				# Display the image with bounding boxes
				

				sentences = []
				
				for group in bbox_groups:
					delimiter = " "  # You can choose any delimiter you want
					sentence = delimiter.join(recatangle_group.text for recatangle_group in bbox_groups[group])
					print(sentence)
					if not any(char.isspace() for char in sentence):
						continue
					sentences.append(sentence)
				os.remove("./Modes/dummy.bin")
				cv2.imshow("res", cv2.resize(frameRgb, (0, 0), fx=.7, fy=.7))
				
				send_json(locate_socket, sentences)
			cv2.imshow("framergb", cv2.resize(frameRgb, (0, 0), fx=.7, fy=.7))

			#speech = result_queue.get() 
			#closest_match = find_closest_match(speech, objects)
			#print(closest_match)
			key = cv2.waitKey(1)
			if key == ord('q'):
				break
			elif key == ord('c'):
				send_json(locate_socket, sentences)