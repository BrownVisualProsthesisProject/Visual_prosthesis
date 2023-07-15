from gtts import gTTS
import pygame

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
        tts = gTTS(sentence, lang='en', slow=False)
        tts.save("./audios/sentence.mp3") 
        sound = pygame.mixer.Sound("./audios/sentence.mp3")
        sound.play()
    
    def describe_pos_w_depth(self, cont_classes, clock):

        sentence = ""
        num_items = len(cont_classes)
        for cls in cont_classes:
            num_items-=1
            if len(cont_classes)>1 and num_items == 0:
                sentence+="and "
            if len(cont_classes[cls]) > 1:
                sentence+="multiple " + make_plural(cls)
            else:
                sentence+= cls
            sentence+=","   

        if len(cont_classes[cls]) > 1:
            sentence += f" at-{clock}-oclock, the-closest at{min(cont_classes[cls])}-feet"
        else:
            sentence += f" at-{clock}-oclock, at{cont_classes[cls][0]}-feet"

        print(sentence)
        tts = gTTS(sentence, lang='en', slow=False)
        tts.save("./audios/sentence.mp3") 

        sound = pygame.mixer.Sound("./audios/sentence.mp3")
        sound.play()

    def describe_position(self, cont_classes, clock):
        
        sentence = ""
        num_items = len(cont_classes)
        for cls in cont_classes:
            num_items-=1
            if len(cont_classes)>1 and num_items == 0:
                sentence+="and "
            if cont_classes[cls] > 1:
                sentence+="multiple " + make_plural(cls)
            else:
                sentence+= cls
            sentence+=","   

        sentence += f" at-{clock}-oclock"             
        print(sentence)
        tts = gTTS(sentence, lang='en', slow=False)
        tts.save("./audios/sentence.mp3") 

        sound = pygame.mixer.Sound("./audios/sentence.mp3")
        sound.play()


    def describe_scene(self, cont_classes, clock, rho=0, theta=90, phi=0):

        sentence = ""
        num_items = len(cont_classes)
        for cls in cont_classes:
            num_items-=1
            if len(cont_classes)>1 and num_items == 0:
                sentence+="and "
            if cont_classes[cls] > 1:
                sentence+="multiple " + make_plural(cls)
            else:
                sentence+= cls
            sentence+=","   

        sentence += f" in-the-scene"             
        print(sentence)
        tts = gTTS(sentence, lang='en', slow=False)
        tts.save("./audios/sentence.mp3") 

        sound = pygame.mixer.Sound("./audios/sentence.mp3")
        sound.play()

