import torch
from TTS.api import TTS
import numpy as np
import sounddevice as sd

from Constants import LABELS

def make_plural(string):
    if string.endswith(('s', 'x', 'z', 'ch', 'sh')):
        return f'{string}es'
    else:
        return f'{string}s'

class Sound_System():
    def __init__(self):
        # Force Coqui TTS to use CPU
        device = "cpu"
        model_name = "tts_models/en/ljspeech/tacotron2-DDC"

        #  english models
        # #"tts_models/en/ljspeech/glow-tts"
        # #"tts_models/en/ljspeech/tacotron2-DDC"
        # #"tts_models/en/ljspeech/tacotron2-DDC"
        #"tts_models/de/thorsten/tacotron2-DDC" 

        self.tts = TTS(model_name=model_name, progress_bar=False).to(device)
    
    def say_sentence(self, sentence): 
        self.play_words(sentence)
    
    def play_words(self, sentence):
        # Generate audio data with Coqui TTS
        wav = self.tts.tts(text=sentence)
        wav = np.array(wav, dtype=np.float32)

        # Play the audio
        sd.play(wav, samplerate=22050)  # Make sure the samplerate is correct for your model
        sd.wait()
    
    def describe_pos_w_depth(self, cont_classes, clock):

        sentence = ""
        num_items = len(cont_classes)
        for cls in cont_classes:
            num_items-=1
            if len(cont_classes)>1 and num_items == 0:
                sentence+="and "
            if len(cont_classes[cls]) > 1:
                sentence+="multiple-" + make_plural(LABELS[cls])
            else:
                sentence+= LABELS[cls]
            sentence+=" "

        if len(cont_classes[cls]) > 1:
            if cont_classes[cls][0]<1.0:
                sentence += f" at-{clock} the-closest at-less-than-1-feet"
            else:
                sentence += f" at-{clock} the-closest at{min(cont_classes[cls])}-feet"
            
        else:
            
            if cont_classes[cls][0]<1.0:
                sentence += f" at-{clock} at-less-than-1-feet"
            elif cont_classes[cls][0]>25.0:
                sentence += f" at-{clock} at-over-25-feet" 
            else:
                sentence += f" at-{clock} at{cont_classes[cls][0]}-feet" 
                
            

        self.play_words(sentence)
        return sentence

    def describe_position(self, cont_classes, clock):
        
        sentence = ""
        num_items = len(cont_classes)
        for cls in cont_classes:
            num_items-=1
            if len(cont_classes)>1 and num_items == 0:
                sentence+="and "
            if cont_classes[cls] > 1:
                sentence+="multiple-" + make_plural(LABELS[cls])
            else:
                sentence+= LABELS[cls]  
            sentence+=" "

        sentence += f" at-{clock}"             

        self.play_words(sentence)
        return sentence


    def describe_scene(self, cont_classes, clock, rho=0, theta=90, phi=0):

        sentence = ""
        num_items = len(cont_classes)
        for cls in cont_classes:
            num_items-=1
            if len(cont_classes)>1 and num_items == 0:
                sentence+="and "
            if cont_classes[cls] > 1:
                sentence+="multiple-" + make_plural(LABELS[cls])
            else:
                sentence+= LABELS[cls] 
            sentence+=" "

        sentence += f" in-the-scene"             

        self.play_words(sentence)
        return sentence
    
    def close_mixer(self):
        # No mixer to close in Coqui TTS
        pass