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
import requests
import pygame
import cv2
#from easyocr import Reader
import numpy as np
from tts import load_model
from ocr_utils.rectangle import BoundingBox
import tesserocr
from tesserocr import PSM, OEM
import re
from PIL import Image
from datetime import datetime

os.environ['TESSDATA_PREFIX'] = "/usr/share/tesseract-ocr/5/tessdata/"

def split_long_numbers(text):
    # Function to split long numbers into groups of 2 or 3
    def split_match(match):
        number = match.group(0)
        length = len(number)
        if length >= 5:
            # Split into groups of 2 or 3
            if length % 2 == 0:
                return ' '.join([number[i:i+2] for i in range(0, length, 2)])
            else:
                # For odd lengths, use one group of 3 and the rest groups of 2
                groups = [number[:3]]
                groups += [number[i:i+2] for i in range(3, length, 2)]
                return ' '.join(groups)
        return number
    
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


def send_json(locate_socket, ocr, close):
    """Sends json data for sound system."""
    messagedata = {
            "raw_ocr": ocr,
            "close": close
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
    camRgb.initialControl.AutoFocusMode(dai.RawCameraControl.AutoFocusMode.AUTO)
    camRgb.setFps(60)
    camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_4_K)

    controlIn = pipeline.create(dai.node.XLinkIn)
    controlIn.setStreamName('control')
    controlIn.out.link(camRgb.inputControl)

    xout = pipeline.create(dai.node.XLinkOut)
    xout.setStreamName("out")
    camRgb.isp.link(xout.input)
    camRgb.setIspScale(3,4)

    counter = 0
    # Initialize Pygame
    pygame.init()
    pygame.mixer.quit()
    pygame.mixer.init(16000, -16, 2)

    # Initialize EasyOCR reader
    #import PIL
    #PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
    #reader = Reader(['en'], recog_network="english_g2")
    # Initialize TTS
    classifier = load_model()

    #warm llm
    data = {
            "model": "mistral-small",
        }
    try:
        response = requests.post(url, json=data, timeout=1)  # Set timeout to 1 second
    except:
        print("LLM loaded")

    # Connect to device and start pipeline
    with dai.Device(pipeline) as device:
        q = device.getOutputQueue(name="out")

        #HFOV = np.deg2rad(90.0)
        frame_count = 0
        start_time = time.time()
        aux = False

        while True:
            frameRgb = q.get().getCvFrame()

            if aux:
                # Convert OpenCV image (NumPy array) to PIL image
                image_pil = Image.fromarray(frameRgb)

                # Perform OCR on the image using tesserocr
                ocr_text = tesserocr.image_to_text(image_pil)
                #os.remove("./Modes/dummy.bin")
                
                
                
                cv2.imshow("res", cv2.resize(frameRgb, (0, 0), fx=.7, fy=.7))

                send_json(locate_socket, ocr_text , False)
                aux = False

            cv2.imshow("framergb", cv2.resize(frameRgb, (0, 0), fx=.7, fy=.7))

            #speech = result_queue.get() 
            #closest_match = find_closest_match(speech, objects)
            #print(closest_match)
            key = cv2.waitKey(1)
            if key == ord('q'):
                send_json(locate_socket, [], True)
                break
            if key == ord('t'):
                aux = True