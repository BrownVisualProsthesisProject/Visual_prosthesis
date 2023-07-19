import pygame
import time
from Constants import LABELS

def make_plural(string):
    if string.endswith(('s', 'x', 'z', 'ch', 'sh')):
        return f'{string}es'
    else:
        return f'{string}s'


class Sound_System():

    def __init__(self):
        pygame.init()

        pygame.mixer.init()
    
    def say_sentence(self, sentence): 
        self.play_words(sentence)
    
    def play_words(self,sentence):
        sentence = sentence.split()

        for word in sentence:
            sound_file = f"./audios/{word}.wav"
            try:
                sound = pygame.mixer.Sound(sound_file)
                sound.play()
                time.sleep(sound.get_length()-.15)  #
            except pygame.error:
                print(f"Sound file not found for word: {word}")

    
    def describe_pos_w_depth(self, cont_classes, clock):

        sentence = ""
        num_items = len(cont_classes)
        for cls in cont_classes:
            num_items-=1
            if len(cont_classes)>1 and num_items == 0:
                sentence+="and "
            if len(cont_classes[cls]) > 1:
                sentence+="multiple " + make_plural(LABELS[cls])
            else:
                sentence+= LABELS[cls]
            sentence+=" "

        if len(cont_classes[cls]) > 1:
            if cont_classes[cls][0]<1.0:
                sentence += f" at-{clock}-oclock the-closest at-less-than-1-feet"
            else:
                sentence += f" at-{clock}-oclock the-closest at{min(cont_classes[cls])}-feet"
            
        else:
            
            if cont_classes[cls][0]<1.0:
                sentence += f" at-{clock}-oclock at-less-than-1-feet" 
            else:
                sentence += f" at-{clock}-oclock at{cont_classes[cls][0]}-feet" 
                
            

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
                sentence+="multiple " + make_plural(LABELS[cls])
            else:
                sentence+= LABELS[cls]  
            sentence+=" "

        sentence += f" at-{clock}-oclock"             

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
                sentence+="multiple " + make_plural(LABELS[cls])
            else:
                sentence+= LABELS[cls] 
            sentence+=" "

        sentence += f" in-the-scene"             

        self.play_words(sentence)
        return sentence
    
    def close_mixer():
        pygame.mixer.quit()

