"""Grasping module with Yolov5."""

# Standar modules
import json
import random
import sys

# Third party modules
import cv2
import numpy as np
import torch
import zmq

# Local modules
from Video_stream_sub import VideoStreamSubscriber

def send_json(locate_socket, x_locs, detected_classes, mode):
    """Sends json data for sound system."""
    messagedata = {
            "locs": x_locs,
            "labels": detected_classes,
            "random": random.randint(1, sys.maxsize),
            "mode": mode,
        }

    obj = json.dumps(messagedata)
    locate_socket.send_string(obj)

if __name__ == "__main__":

    context = zmq.Context()
    locate_socket = context.socket(zmq.PUB)
    locate_socket.bind("tcp://127.0.0.1:5559")

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

    hostname = "127.0.0.1"  # Use to receive from localhost
    # hostname = "192.168.86.38"  # Use to receive from other computer
    port = 5557

    imagehub = VideoStreamSubscriber(hostname, port)

    # Grab new frame.
    host_name, frame = imagehub.recv_image()
    frame = cv2.imdecode(np.frombuffer(frame, dtype="uint8"), -1)

    # Get frame shape.
    x_shape, y_shape = frame.shape[1], frame.shape[0]

    topic = 1000

    key_stroke_counter = 0
    mode = ""
    while True:
        # Grab new frame.
        host_name, frame = imagehub.recv_image()
        frame = cv2.imdecode(np.frombuffer(frame, dtype="uint8"), -1)
        
        # Run object detection inference over frame.
        results = model(frame)

        # Get labels and bounding boxes coordinates.
        labels = results.xyxyn[0][:, -1].cpu().numpy()
        cord = results.xyxyn[0][:, :-1].cpu().numpy()
        x_locs = []
        detected_classes = []

        for i in range(len(labels)):
            row = cord[i]
            # If confidence score is less than 0.45 we avoid making a prediction.
            if row[4] < 0.45:
                continue

            x1 = int(row[0] * x_shape)
            y1 = int(row[1] * y_shape)
            x2 = int(row[2] * x_shape)
            y2 = int(row[3] * y_shape)

            x = x1 + (x2 - x1) // 2

            # Plot the boxes and text.
            cv2.rectangle(frame, (x1, y1), (x2, y2), bgr, 2)
            cv2.putText(frame, classes[int(labels[i])], (x1, y1), label_font, 2, bgr, 2)

            x_locs.append(x / x_shape)
            detected_classes.append(classes[int(labels[i])])

        # Show processed frame.
        cv2.imshow("processed frame", frame)
        key_pressed = cv2.waitKey(1)
        if key_pressed == ord("/") or key_pressed == ord("7"):
            mode = "d"
        elif key_pressed == ord("*") or key_pressed == ord("-"):
            mode = "l"

        if mode != "":
            if key_stroke_counter < 3:
                key_stroke_counter+=1
            else:
                mode = ""
                key_stroke_counter = 0
        
        print("The mode is ", mode)
        # Do not send information to sound system when len(detected_classes)==0.
        if not x_locs:
            continue

        send_json(locate_socket, x_locs, detected_classes, mode)