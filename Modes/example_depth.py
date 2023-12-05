#!/usr/bin/env python3

import cv2
import depthai as dai
import numpy as np

# Closer-in minimum depth, disparity range is doubled (from 95 to 190):
extended_disparity = False
# Better accuracy for longer distance, fractional disparity 32-levels:
subpixel = True
# Better handling for occlusions:
lr_check = True

# Create pipeline
pipeline = dai.Pipeline()

# Define sources and outputs
monoLeft = pipeline.create(dai.node.MonoCamera)
monoRight = pipeline.create(dai.node.MonoCamera)
stereo = pipeline.create(dai.node.StereoDepth)
xoutDisp = pipeline.create(dai.node.XLinkOut)
xoutDisp.setStreamName("disparity")
xoutDepth = pipeline.create(dai.node.XLinkOut)
xoutDepth.setStreamName("depth")

sensorRes = dai.MonoCameraProperties.SensorResolution.THE_480_P

# Properties
monoLeft.setResolution(sensorRes)
monoLeft.setCamera("left")
monoRight.setResolution(sensorRes)
monoRight.setCamera("right")

imgSize = monoLeft.getResolutionSize()

# Create a node that will produce the depth map (using disparity output as it's easier to visualize depth this way)
stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
stereo.setLeftRightCheck(lr_check)
stereo.setExtendedDisparity(extended_disparity)
stereo.setSubpixel(subpixel)

alpha = None
alpha = 0
if alpha is not None:
    stereo.setAlphaScaling(alpha)

# Linking
monoLeft.out.link(stereo.left)
monoRight.out.link(stereo.right)
stereo.disparity.link(xoutDisp.input)
stereo.depth.link(xoutDepth.input)

device = dai.Device()

calibData = device.readCalibration()

socket = dai.CameraBoardSocket.CAM_C

cameraModel = calibData.getDistortionModel(socket)
if cameraModel != dai.CameraModel.Perspective:
    print("This script handles only perspective camera model")
    exit(1)

M = np.array(calibData.getCameraIntrinsics(socket, imgSize[0], imgSize[1]))
d = np.array(calibData.getDistortionCoefficients(socket))

if alpha == None:
    M_new = M
else:
    M_new, _ = cv2.getOptimalNewCameraMatrix(M, d, imgSize, alpha)

focal = M_new[0][0]
baseline = abs(calibData.getBaselineDistance(dai.CameraBoardSocket.CAM_B, dai.CameraBoardSocket.CAM_C))*10
subpixel = stereo.initialConfig.get().algorithmControl.enableSubpixel
subpixelLevels = pow(2, stereo.initialConfig.get().algorithmControl.subpixelFractionalBits) if subpixel else 1

scale = baseline * focal * subpixelLevels
print(f"baseline {baseline} mm")
print(f"focal {focal}")
print(f"scale {scale}")

print(f"old: {M}")
print(f"new: {M_new}")

# Connect to device and start pipeline
with device:

    device.startPipeline(pipeline)

    # Output queue will be used to get the disparity frames from the outputs defined above
    q = device.getOutputQueue(name="disparity", maxSize=4, blocking=True)
    qDepth = device.getOutputQueue(name="depth", maxSize=4, blocking=True)

    while True:
        inDisparity = q.get()  # blocking call, will wait until a new data has arrived
        inDepth = qDepth.get()  # blocking call, will wait until a new data has arrived

        dispData = inDisparity.getFrame()
        depthData = inDepth.getFrame()
        hostDepthFrame = np.zeros(depthData.shape, np.uint16)
        with np.errstate(divide='ignore'):
            hostDepthFrame = scale / dispData
        hostDepthFrame[dispData == 0] = 0
        hostDepthFrame = np.rint(hostDepthFrame)
        hostDepthFrame[hostDepthFrame > 65535] = 65535

        diff = (np.sum(np.abs(hostDepthFrame - depthData)))
        print(f"host vs FW depth difference {diff}")

        frame = inDisparity.getFrame()
        # Normalization for better visualization
        frame = (frame * (255 / stereo.initialConfig.getMaxDisparity())).astype(np.uint8)

        cv2.imshow("disparity", frame)

        frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)
        cv2.imshow("disparity_color", frame)

        if cv2.waitKey(1) == ord('q'):
            break