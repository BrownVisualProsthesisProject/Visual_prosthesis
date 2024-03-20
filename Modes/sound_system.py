import pygame
import time
from Constants import LABELS, PLURALS

class Sound_System():

    def __init__(self):
        pygame.init()

        pygame.mixer.init()
    
    def say_sentence(self, sentence): 
        self.play_words(sentence)
    
    def play_words(self,sentence):
        sentence = sentence.split("_")
        print(sentence)
        for word in sentence:
            if word == "":
                continue
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
                sentence+="and_"
            if len(cont_classes[cls]) > 1:
                sentence+="multiple-" + PLURALS[cls]
            else:
                sentence+= LABELS[cls]
            sentence+="_"

        if len(cont_classes[cls]) > 1:
            if cont_classes[cls][0]<1.0:
                sentence += f"_at-{clock}_the-closest_at-less-than-1-feet"
            else:
                sentence += f"_at-{clock}_the-closest_at{min(cont_classes[cls])}-feet"
            
        else:
            
            if cont_classes[cls][0]<1.0:
                sentence += f"_at-{clock}_at-less-than-1-feet"
            elif cont_classes[cls][0]>25.0:
                sentence += f"_at-{clock}_at-over-25-feet" 
            else:
                sentence += f"_at-{clock}_at{cont_classes[cls][0]}-feet" 
                
            

        self.play_words(sentence)
        return sentence

    def describe_position(self, cont_classes, clock):
        
        sentence = ""
        num_items = len(cont_classes)
        for cls in cont_classes:
            num_items-=1
            if len(cont_classes)>1 and num_items == 0:
                sentence+="and_"
            if cont_classes[cls] > 1:
                sentence+="multiple-" + PLURALS[cls]
            else:
                sentence+= LABELS[cls]  
            sentence+="_"

        sentence += f"_at-{clock}"             

        self.play_words(sentence)
        return sentence


    def describe_scene(self, cont_classes, clock, rho=0, theta=90, phi=0):

        sentence = ""
        num_items = len(cont_classes)
        for cls in cont_classes:
            num_items-=1
            if len(cont_classes)>1 and num_items == 0:
                sentence+="and_"
            if cont_classes[cls] > 1:
                sentence+="multiple-" + PLURALS[cls]
            else:
                sentence+= LABELS[cls] 
            sentence+="_"

        sentence += f"_in-the-scene"             

        self.play_words(sentence)
        return sentence
    
    def close_mixer(self):
        pygame.mixer.quit()

