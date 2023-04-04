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
    
    def describe_position(self, cont_classes, clock, understand_flag=True, rho=0, theta=90, phi=0):
        
        if not understand_flag:
            sentence = "Sorry, I can't locate that."
            tts = gTTS(sentence, lang='en', slow=False)
            tts.save("./audios/sentence.mp3") 
            sound = pygame.mixer.Sound("./audios/sentence.mp3")
            sound.play()
            return

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

        sentence += f" at {clock} o clock"             
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

        sentence += f" in the scene"             
        print(sentence)
        tts = gTTS(sentence, lang='en', slow=False)
        tts.save("./audios/sentence.mp3") 

        sound = pygame.mixer.Sound("./audios/sentence.mp3")
        sound.play()

