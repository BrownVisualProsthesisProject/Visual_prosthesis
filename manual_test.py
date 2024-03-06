import pygame
import time
from Modes.Constants import LABELS
import string
from rapidfuzz import fuzz
import platform
import time


if platform.machine() == "aarch64":
	import Jetson.GPIO as GPIO

class Sound_System():
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
    
    def play_words(self, sentence):
        pygame.init()
        pygame.mixer.init()

        sentence = sentence.split()

        for word in sentence:
            sound_file = f"./audios/{word}.wav"
            try:
                sound = pygame.mixer.Sound(sound_file)
                sound.play()
                time.sleep(sound.get_length() - 0.15)
            except pygame.error:
                print(f"Sound file not found for word: {word}")

    def close_mixer(self):
        pygame.mixer.quit()

def find_closest_match(word):
	max_score = -1
	closest_match = None
	word_cleaned = word.translate(str.maketrans('', '', string.punctuation)).lower()
	print(word_cleaned)
	for key in LABELS:
		score = fuzz.ratio(word_cleaned, LABELS[key])
		if score > .6 and score > max_score :
			max_score = score
			closest_match = key

	return LABELS[closest_match]


if platform.machine() == "aarch64":
    GPIO.setmode(GPIO.BOARD)
    channel = 16
    GPIO.setup(channel, GPIO.OUT)
# Example usage:
sound_system = Sound_System()
times = ["ten-oclock","ten-thirty","eleven-oclock","eleven-thirty","twelve-oclock","twelve-thirty","one-oclock", "one-thirty", "two-oclock"]

while True:
    sentence = input("Enter word and time (type 'q' to quit): ")
    
    if sentence.lower() == 'q':
        break
    label, clock = sentence.split()
    if not clock.isdigit() or int(clock) > len(times):
        print("Invalid input. Please enter an integer less than 10.")
        continue
    label = find_closest_match(label)
    sentence = f"{label} at-{times[-int(clock)]} at10.0-feet"
    sound_system.play_words(sentence)

    if platform.machine() == "aarch64":
        GPIO.output(channel, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(channel, GPIO.LOW)

sound_system.close_mixer()
