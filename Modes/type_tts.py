import pygame
import wave
import numpy as np
import time 
from tts import load_model

def play_sentence(sentence, classifier, save_as_wav=False):
    if sentence == "":
        return 
    
    # Classify the sentence and get the NumPy array and sample rate
    npa, sample_rate = classifier(sentence)
    # Ensure the NumPy array is in the correct shape (two channels, stereo)
    npa = np.repeat(npa.reshape(len(npa), 1), 2, axis=1)
    
    # Play the audio using PyGame
    sound = pygame.sndarray.make_sound(npa)
    sound.play()
    pygame.time.wait(int(sound.get_length() * 1000))
    
    # Optionally, save the sound to a .wav file
    if save_as_wav:
        # Initialize PyGame mixer if needed
        pygame.mixer.init(frequency=sample_rate, size=-16, channels=2)
        
        # Generate a simple timestamp in the format YYYYMMDD_HHMMSS
        timestamp = int(time.time())
        wav_filename = f"./table/output_{timestamp}.wav"
        
        with wave.open(wav_filename, 'w') as sfile:
            # Set parameters for the wave file (sample rate, stereo, 16-bit)
            sfile.setframerate(sample_rate)
            sfile.setnchannels(2)  # Stereo
            sfile.setsampwidth(2)  # 2 bytes for 16-bit audio
            
            # Scale and convert the NumPy array to int16 for 16-bit PCM format
            # First, normalize the array if it's not already in the correct range
            max_val = np.max(np.abs(npa))  # Find the max value for normalization
            if max_val > 0:
                npa_normalized = npa / max_val  # Normalize to [-1, 1] range
            else:
                npa_normalized = npa
            
            # Convert the normalized array to int16 PCM format
            npa_int16 = (npa_normalized * 32767).astype(np.int16)
            
            # Write the audio data to the wave file
            sfile.writeframes(npa_int16.tobytes())
        
        print(f"Audio saved as {wav_filename}")

pygame.mixer.init(frequency=22050, size=-16, channels=2)

classifier = load_model()
s = "Cell phone "

play_sentence(s, classifier)
s = "at one o'clock at ten feet"

play_sentence(s, classifier)