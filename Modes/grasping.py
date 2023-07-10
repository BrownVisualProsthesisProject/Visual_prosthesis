"""Grasping module with Yolov5."""

# Standard modules
import json
import random
import sys
import math

# Third party modules
import cv2
import numpy as np
import torch
import zmq
import depthai as dai
import time 

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

if __name__ == "__main__":

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

	matching_counter = 5


	counter = 0

		# Connect to device and start pipeline
	with device:
		device.startPipeline(pipeline)

		frameRgb = None
		depthFrame = None

		device.setIrLaserDotProjectorBrightness(0) # in mA, 0..1200
		device.setIrFloodLightBrightness(0) # in mA, 0..1500

		x_shape, y_shape = (1280,720)
		#x_shape, y_shape = (1248, 936) #with set outputsize
		latestPacket = {}
		latestPacket["rgb"] = None
		latestPacket["depth"] = None
		HFOV = np.deg2rad(69.0)
		#HFOV = np.deg2rad(90.0)
		frame_count = 0
		start_time = time.time()

		while True:

			# Perform object detection every odd frame
			#if counter % 2 == 0:
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
				min_depth = np.percentile(depthAux, 1)
				max_depth = np.percentile(depthFrame, 99)
				depthFrameColor = np.interp(depthFrame, (min_depth, max_depth), (0, 255)).astype(np.uint8)
				#depthFrameColor = cv2.applyColorMap(depthFrameColor, cv2.COLORMAP_JET)
				#cv2.imshow("depth", depthFrameColor)

			if frameRgb is not None and depthFrame is not None:
				# Run object detection inference over frame.
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
					cv2.rectangle(frameRgb, (x1, y1), (x2, y2), bgr, 2)
					cv2.putText(frameRgb, classes[int(labels[i])], (x1, y1), label_font, 2, bgr, 2)
					cv2.putText(frameRgb, "{:.1f} m".format(distance/1000), (x1 + 10, y1 + 20), label_font, 0.7, (0,100,255))
	
					x_locs[i] = x / x_shape
					y_locs[i] = y / y_shape
					detected_classes[i] = classes[int(labels[i])]
					object_depth[i] = distance
				
				send_json(locate_socket, x_locs, y_locs, x_shape, y_shape, detected_classes, object_depth)
				#blended_frame = cv2.addWeighted(frameRgb, .7, depthFrameColor, .3 , 0)
				# Increment frame count
				frame_count += 1
				
				# Calculate FPS
				end_time = time.time()
				elapsed_time = end_time - start_time
				fps = frame_count / elapsed_time
				cv2.putText(frameRgb, "FPS: {:.2f}".format(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
				cv2.imshow("Blended Frame", frameRgb)

			if cv2.waitKey(1) == ord('q'):
				break

			
