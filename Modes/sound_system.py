#import pygame
import time
import platform
from Constants import LABELS

# Conditional imports based on the OS
if platform.system() == "Darwin":
    from AppKit import NSSpeechSynthesizer
else:
    import pyttsx3

def make_plural(string):
    if string.endswith(('s', 'x', 'z', 'ch', 'sh')):
        return f'{string}es'
    else:
        return f'{string}s'

class Sound_System():

    voice_choice = 108  # voice to desired index

    def __init__(self):
        if platform.system() == "Darwin":
            self.synthesizer = NSSpeechSynthesizer.alloc().init()
            self.synthesizer.setRate_(150.0)
            
            # Set the voice based on voice_choice
            voices = NSSpeechSynthesizer.availableVoices()
            self.synthesizer.setVoice_(voices[self.voice_choice])
            
        else:
            self.engine = pyttsx3.init()
            rate = self.engine.getProperty('rate')
            self.engine.setProperty('rate', rate)

    def say_sentence(self, sentence): 
        self.play_words(sentence)
    
    def play_words(self, sentence):
        if platform.system() == "Darwin":
            self.synthesizer.startSpeakingString_(sentence)
            time.sleep(len(sentence) * 0.1)
        else:
            self.engine.say(sentence)
            self.engine.runAndWait()

    def describe_pos_w_depth(self, cont_classes, clock):
        sentence = ""
        num_items = len(cont_classes)
        for cls in cont_classes:
            num_items -= 1
            if len(cont_classes) > 1 and num_items == 0:
                sentence += "and "
            if len(cont_classes[cls]) > 1:
                sentence += "multiple-" + make_plural(LABELS[cls])
            else:
                sentence += LABELS[cls]
            sentence += " "

        if len(cont_classes[cls]) > 1:
            if cont_classes[cls][0] < 1.0:
                sentence += f" at-{clock} the-closest at-less-than-1-feet"
            else:
                sentence += f" at-{clock} the-closest at{min(cont_classes[cls])}-feet"
        else:
            if cont_classes[cls][0] < 1.0:
                sentence += f" at-{clock} at-less-than-1-feet"
            elif cont_classes[cls][0] > 25.0:
                sentence += f" at-{clock} at-over-25-feet"
            else:
                sentence += f" at-{clock} at{cont_classes[cls][0]}-feet"

        self.play_words(sentence)
        return sentence

    def describe_position(self, cont_classes, clock):
        sentence = ""
        num_items = len(cont_classes)
        for cls in cont_classes:
            num_items -= 1
            if len(cont_classes) > 1 and num_items == 0:
                sentence += "and "
            if cont_classes[cls] > 1:
                sentence += "multiple-" + make_plural(LABELS[cls])
            else:
                sentence += LABELS[cls]
            sentence += " "

        sentence += f" at-{clock}"

        self.play_words(sentence)
        return sentence

    def describe_scene(self, cont_classes, clock, rho=0, theta=90, phi=0):
        sentence = ""
        num_items = len(cont_classes)
        for cls in cont_classes:
            num_items -= 1
            if len(cont_classes) > 1 and num_items == 0:
                sentence += "and "
            if cont_classes[cls] > 1:
                sentence += "multiple-" + make_plural(LABELS[cls])
            else:
                sentence += LABELS[cls]
            sentence += " "

        sentence += " in-the-scene"

        self.play_words(sentence)
        return sentence
    
    def close_mixer(self):
        if platform.system() != "Darwin":
            self.engine.stop()
        else:
            self.engine.stop()