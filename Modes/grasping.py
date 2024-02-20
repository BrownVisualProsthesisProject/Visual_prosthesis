"""Grasping module with Yolov5."""

# Standard modules
import json
import random
import sys
import math

# Third party modules
import argparse
import cv2
import numpy as np
import torch
import zmq
import depthai as dai
import time 

UNWARP_ALPHA = .01

def getUndistortMap(calibData, ispSize):
	M1 = np.array(calibData.getCameraIntrinsics(dai.CameraBoardSocket.RIGHT, ispSize[0], ispSize[1]))
	d1 = np.array(calibData.getDistortionCoefficients(dai.CameraBoardSocket.RIGHT))

	R1 = None   #np.identity(3)

	M2, _= cv2.getOptimalNewCameraMatrix(
														M1,
														d1,
														ispSize,
														UNWARP_ALPHA,
														ispSize,
														False
													)


	return cv2.initUndistortRectifyMap(M1, d1, R1, M2, ispSize, cv2.CV_32FC1)


def getMesh(calibData: dai.CalibrationHandler, ispSize, focal_len_scaling_factor: float = .8):
	M1 = np.array(calibData.getCameraIntrinsics(dai.CameraBoardSocket.RIGHT, ispSize[0], ispSize[1]))
	d1 = np.array(calibData.getDistortionCoefficients(dai.CameraBoardSocket.RIGHT))
	R1 = np.identity(3)
	M1_new = M1.copy()
	M1_new[0][0] *= focal_len_scaling_factor
	M1_new[1][1] *= focal_len_scaling_factor
	mapX, mapY = cv2.initUndistortRectifyMap(M1, d1, R1, M1_new, ispSize, cv2.CV_32FC1)

	meshCellSize = 16
	mesh0 = []
	# Creates subsampled mesh which will be loaded on to device to undistort the image
	for y in range(mapX.shape[0] + 1): # iterating over height of the image
		if y % meshCellSize == 0:
			rowLeft = []
			for x in range(mapX.shape[1]): # iterating over width of the image
				if x % meshCellSize == 0:
					if y == mapX.shape[0] and x == mapX.shape[1]:
						rowLeft.append(mapX[y - 1, x - 1])
						rowLeft.append(mapY[y - 1, x - 1])
					elif y == mapX.shape[0]:
						rowLeft.append(mapX[y - 1, x])
						rowLeft.append(mapY[y - 1, x])
					elif x == mapX.shape[1]:
						rowLeft.append(mapX[y, x - 1])
						rowLeft.append(mapY[y, x - 1])
					else:
						rowLeft.append(mapX[y, x])
						rowLeft.append(mapY[y, x])
			if (mapX.shape[1] % meshCellSize) % 2 != 0:
				rowLeft.append(0)
				rowLeft.append(0)

			mesh0.append(rowLeft)

	mesh0 = np.array(mesh0)
	meshWidth = mesh0.shape[1] // 2
	meshHeight = mesh0.shape[0]
	mesh0.resize(meshWidth * meshHeight, 2)

	mesh = list(map(tuple, mesh0))

	return mesh, meshWidth, meshHeight

def calc_angle(frame, offset, HFOV):
	return math.atan(math.tan(HFOV / 2.0) * offset / (frame.shape[1] / 2.0))

def getHFov(intrinsics, width):
	fx = intrinsics[0][0]
	fov = 2 * 180 / (math.pi) * math.atan(width * 0.5 / fx)
	return fov

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
	rgbResolution = dai.ColorCameraProperties.SensorResolution.THE_720_P

	# Create pipeline
	
	pipeline = dai.Pipeline()
	device = dai.Device()
	calibData = device.readCalibration2()
	
	queueNames = []

	# Define sources and outputs
	left = pipeline.create(dai.node.ColorCamera)
	right = pipeline.create(dai.node.ColorCamera)
	stereo = pipeline.create(dai.node.StereoDepth)

	try:
		calibData = device.readCalibration2()
		lensPosition = calibData.getLensPosition(dai.CameraBoardSocket.RGB)
		if lensPosition:
			right.initialControl.setManualFocus(lensPosition)
	except:
		raise

	rightOut = pipeline.create(dai.node.XLinkOut)
	depthOut = pipeline.create(dai.node.XLinkOut)

	rightOut.setStreamName("rgb")
	queueNames.append("rgb")
	depthOut.setStreamName("depth")
	queueNames.append("depth")

	
	left.setResolution(rgbResolution)
	left.setBoardSocket(dai.CameraBoardSocket.LEFT)
	left.setFps(fps)
	right.setResolution(rgbResolution)
	right.setBoardSocket(dai.CameraBoardSocket.RIGHT)
	right.setFps(fps)

	#right.initialControl.setSharpness(0)     # range: 0..4, default: 1
	#right.initialControl.setLumaDenoise(0)   # range: 0..4, default: 1
	#right.initialControl.setChromaDenoise(4) # range: 0..4, default: 1
	#left.initialControl.setSharpness(0)     # range: 0..4, default: 1
	#left.initialControl.setLumaDenoise(0)   # range: 0..4, default: 1
	#left.initialControl.setChromaDenoise(4) # range: 0..4, default: 1

	stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
	# LR-check is required for depth alignment
	stereo.initialConfig.setMedianFilter(dai.MedianFilter.KERNEL_7x7)
	stereo.setLeftRightCheck(True)
	stereo.setSubpixel(True)
	stereo.setExtendedDisparity(True) #best 
	#stereo.setOutputSize(812, 608)
	stereo.setDepthAlign(dai.CameraBoardSocket.RIGHT)
	if args.distort:
		stereo.setAlphaScaling(UNWARP_ALPHA)
		stereo.setRectifyEdgeFillColor(0)

	# Linking
	left.isp.link(stereo.left)
	right.isp.link(stereo.right)
	stereo.depth.link(depthOut.input)
	right.isp.link(rightOut.input)

	# Load Yolov5 model.
	model = torch.hub.load('./yolov5', 'custom', path=f'./weights/{args.model}.pt', source='local') 
	model.half() #should I img.half????
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
		calibData = device.readCalibration()
		M, width, height = calibData.getDefaultIntrinsics(dai.CameraBoardSocket.RIGHT)
		M = np.array(M)
		if args.distort:
			mapX, mapY = getUndistortMap(calibData, right.getIspSize())
		frameRgb = None
		depthFrame = None

		#device.setIrLaserDotProjectorBrightness(0) # in mA, 0..1200
		#device.setIrFloodLightBrightness(0) # in mA, 0..1500
		width_resize = 1180
		x_shape, y_shape = (width_resize,720)
		#x_shape, y_shape = (1248, 936) #with set outputsize
		latestPacket = {}
		latestPacket["rgb"] = None
		latestPacket["depth"] = None
		#latestPacket["Undistorted"] = None
		HFOV = getHFov(M, width)
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
				if args.distort:
					frameRgb = cv2.remap(frameRgb, mapX, mapY, cv2.INTER_LINEAR)
				#frameRgb = cv2.resize(frameRgb, (812, 608))
				frameRgb = frameRgb[:,:width_resize]
				cv2.imshow("frameRGB", frameRgb)


			if latestPacket["depth"]:
				depthFrame = latestPacket["depth"].getFrame()
				depthAux = depthFrame[depthFrame != 0]
				if not depthAux.any(): continue
				depthFrame = depthFrame[:, :width_resize]

				min_depth = np.percentile(depthFrame, 1)
				max_depth = np.percentile(depthFrame, 99)
				depthFrameColor = np.interp(depthFrame, (min_depth, max_depth), (0, 255)).astype(np.uint8)
				depthFrameColor = cv2.applyColorMap(depthFrameColor, cv2.COLORMAP_JET)
				cv2.imshow("depth", depthFrameColor)
			

			if frameRgb is not None and depthFrame is not None :
				
				# Run object detection inference over frame.
				with torch.no_grad(): 
					results = model(frameRgb)
				
				# Get labels and bounding boxes coordinates.
				labels = results.xyxyn[0][:, -1].cpu().numpy()
				cord = results.xyxyn[0][:, :-1].cpu().numpy()

				x_locs = [0]*len(labels)
				y_locs = [0]*len(labels)
				detected_classes = [0]*len(labels)
				object_depth = [0]*len(labels)
				new_points = []
				for i in range(len(labels)):
					row = cord[i]
					# If confidence score is less than 0.45 we avoid making a prediction.
					if row[4] < 0.2:
						continue

					x1 = int(row[0] * x_shape) 
					y1 = int(row[1] * y_shape)
					x2 = int(row[2] * x_shape)
					y2 = int(row[3] * y_shape)

					x = x1 + (x2 - x1) // 2
					y = y1 + (y2 - y1) // 2

					z = np.median(depthFrame[y1+5:y2-5,x1+5:x2-5])
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
				blended_frame = cv2.addWeighted(frameRgb, .6, depthFrameColor, .4 , 0)
				# Increment frame count
				frame_count += 1
				
				# Calculate FPS
				end_time = time.time()
				elapsed_time = end_time - start_time
				fps = frame_count / elapsed_time
				cv2.putText(blended_frame, "FPS: {:.2f}".format(fps), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
	
				cv2.imshow("Blended Frame", blended_frame)

			if cv2.waitKey(1) == ord('q'):

				break
