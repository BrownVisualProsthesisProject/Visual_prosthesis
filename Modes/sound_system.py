import torch
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from pydub.playback import play
import tempfile

# import pygame
# import time
from Constants import LABELS

def make_plural(string):
    if string.endswith(('s', 'x', 'z', 'ch', 'sh')):
        return f'{string}es'
    else:
        return f'{string}s'

class Sound_System():
    
    def __init__(self):
        # Load Silero TTS model
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model, self.utils = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                                model='silero_tts',
                                                language='en',  # choose the language
                                                speaker='lj')  # choose the speaker
        (self.text_to_speech, _, _) = self.utils

    def say_sentence(self, sentence):
        self.play_words(sentence)

    def play_words(self, sentence):
        # Synthesize speech
        audio = self.text_to_speech(texts=[sentence],
                                    model=self.model,
                                    sample_rate=16000,
                                    symbols_embedding_dim=768)[0]

        # Save and play the audio
        with tempfile.NamedTemporaryFile(delete=True) as temp_wav:
            sf.write(temp_wav.name, audio.numpy(), 16000, format="WAV")
            sound = AudioSegment.from_wav(temp_wav.name)
            play(sound)

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
        # Implement the required mixer close functionality if necessary
        pass

# Example usage
# sound_system = Sound_System()
# sound_system.say_sentence("Hello, this is a test sentence using Silero TTS.")
