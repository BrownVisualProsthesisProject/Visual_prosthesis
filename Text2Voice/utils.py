import pyttsx3

def text2voice():
    engine = pyttsx3.init()
    engine.setProperty('voice', "english_rp+f4")  

    speed_change = -20
    engine.setProperty('rate', engine.getProperty('rate') + speed_change)
    return engine