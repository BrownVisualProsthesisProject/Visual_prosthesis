import pygame
import time
import string
from rapidfuzz import fuzz
import platform
import time
import pandas as pd
from constants import KEY as key


if platform.machine() == "aarch64":
	import Jetson.GPIO as GPIO

class Sound_System():
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
    
    def play_words(self, sentence):
        pygame.init()
        pygame.mixer.init()

        sentence = sentence.split("_")

        for word in sentence:
            sound_file = f"../audios/{word}.wav"
            try:
                sound = pygame.mixer.Sound(sound_file)
                sound.play()
                time.sleep(sound.get_length() - 0.15)
            except pygame.error:
                print(f"Sound file not found for word: {word}")

    def close_mixer(self):
        pygame.mixer.quit()


if platform.machine() == "aarch64":
    GPIO.setmode(GPIO.BOARD)
    channel = 16
    GPIO.setup(channel, GPIO.OUT)
# Example usage:
sound_system = Sound_System()
times = ["ten-thirty","eleven-oclock","eleven-thirty","twelve-oclock","twelve-thirty","one-oclock", "one-thirty"]
file_name = 'close_trials_1_experimental.csv'
file_split = file_name.split("_")
df = pd.read_csv(file_name)

target_position = 'target position'  # Name of the first column
target_label = 'target object'  # Name of the second column
row_index = -1  # Index of the specific row

while True:
    action = input("Enter word and time (type 'q' to quit): ")

    if action == 't':
        if platform.machine() == "aarch64":
            GPIO.output(channel, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(channel, GPIO.LOW)
        continue
    if action == 'q':
        break

    if action.isdigit():
        action_num = int(action)
        if 1 <= action_num <= df.shape[0]:
            row_index = action_num - 1
            info = df.iloc[row_index][[target_position, target_label]]
        else:
            print("Invalid number. Please enter a number within the range of 1 to", df.shape[0])
            continue

    elif action == "n":
        if row_index < df.shape[0]:
            row_index+=1
        else:
            row_index-=1

        # Accessing information from specific row and columns using iloc
        info = df.iloc[row_index][[target_position, target_label]]
    
    elif action == "b":
        if row_index <=0:
            row_index+=1
        else:
            row_index-=1
        # Accessing information from specific row and columns using iloc
        info = df.iloc[row_index][[target_position, target_label]]
        
    print(info[target_label])
    if file_split[-1][0] == "c":
        sentence = f"{key[info[target_label][0]]}"
    else:
        if file_split[0][0] == "c":
            dis = "at3.0-feet"
        else:
            dis = "at10.0-feet"
        sentence = f"{key[info[target_label][0]]}_at-{times[info[target_position]-1]}_{dis}"
    sound_system.play_words(sentence)

    if platform.machine() == "aarch64":
        GPIO.output(channel, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(channel, GPIO.LOW)

sound_system.close_mixer()
