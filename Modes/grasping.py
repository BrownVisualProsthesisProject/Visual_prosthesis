"""Grasping module with Yolov5."""

# Standard modules
import json
import math
import random

# Third party modules
import cv2
import mediapipe as mp
import numpy as np
import zmq
from pydub import AudioSegment
from pydub.playback import play

# Local modules
from Video_stream_sub import VideoStreamSubscriber

if __name__ == "__main__":

    context = zmq.Context()
    locate_socket = context.socket(zmq.PUB)
    locate_socket.bind("tcp://127.0.0.1:5559")

    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_hands = mp.solutions.hands
    BLUE_COLOR = (255, 0, 0)

    hostname = "127.0.0.1"  # Use to receive from localhost
    # hostname = "192.168.86.38"  # Use to receive from other computer
    port = 5557

    imagehub = VideoStreamSubscriber(hostname, port)

    # Grab new frame.
    host_name, frame = imagehub.recv_image()
    frame = cv2.imdecode(np.frombuffer(frame, dtype="uint8"), -1)

    # Get frame shape.
    x_shape, y_shape = frame.shape[1], frame.shape[0]
    random_x = random.randint(40, x_shape - 40)
    random_y = random.randint(40, y_shape - 40)
    random_point = np.array([random_x, random_y])
    audio = AudioSegment.from_wav("./audios/notification.wav")

    with mp_hands.Hands(
        max_num_hands=1,
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as hands:

        while True:

            # Grab new frame.
            host_name, frame = imagehub.recv_image()
            frame = cv2.imdecode(np.frombuffer(frame, dtype="uint8"), -1)
            # Run object detection inference over frame.
            # To improve performance, optionally mark the image as not writeable to
            # pass by reference.
            frame.flags.writeable = False
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame)
            # Draw the hand annotations on the image.
            frame.flags.writeable = True
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    for idx, landmark in enumerate(hand_landmarks.landmark):
                        x_px = min(math.floor(landmark.x * x_shape), x_shape - 1)
                        y_px = min(math.floor(landmark.y * y_shape), y_shape - 1)
                        if idx == 8:
                            frame = cv2.circle(frame, (x_px, y_px), 3, BLUE_COLOR, 3)
                            finger = np.array([x_px, y_px])

                            # Calculate distance between finger and random point
                            distance = np.linalg.norm(random_point - finger)

                            # Check if distance is less than 15
                            if distance < 20:
                                movement = "notification"
                                play(audio)
                                random_x = random.randint(40, x_shape - 40)
                                random_y = random.randint(40, y_shape - 40)
                                random_point = np.array([random_x, random_y])
                            # Else, calculate horizontal and vertical distance
                            else:
                                horizontal_distance = x_px - random_x
                                vertical_distance = y_px - random_y

                                # Check if horizontal distance is greater than vertical distance
                                if abs(horizontal_distance) > abs(vertical_distance):
                                    # Check if finger is to the right or left of random point
                                    if horizontal_distance > 0:
                                        movement = "left"
                                    else:
                                        movement = "right"
                                # Else, check if finger is above or below random point
                                else:
                                    if vertical_distance > 0:
                                        movement = "up"
                                    else:
                                        movement = "down"

                            messagedata = {
                                "move": movement,
                            }
                            obj = json.dumps(messagedata)
                            locate_socket.send_string(obj)

                        else:
                            frame = cv2.circle(frame, (x_px, y_px), 2, (0, 0, 222), 2)

            frame = cv2.circle(frame, (random_x, random_y), 3, (0, 0, 222), 10)

            # Flip the image horizontally for a selfie-view display.
            cv2.imshow("MediaPipe Hands", cv2.flip(frame, 1))
            if cv2.waitKey(5) & 0xFF == 27:
                break

            
