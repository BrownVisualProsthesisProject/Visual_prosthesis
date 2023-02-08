import math as m
import os

from openal.audio import SoundSink, SoundSource, SoundListener
from openal.loaders import load_wav_file
import time

class Sound_System():

    def __init__(self):
        self.sink = SoundSink()
        self.sink.activate()
        self.listener = SoundListener()
        self.sink.listener = self.listener
        self.listener.position = (0, 0, 0)
        self.listener.velocity = (0, 0, 0)

        # Orientation described as an X, Y, Z "at" vector and an X, Y, Z "up" vector.
        # The values assigned above were chosen to match with our universal head-relative spherical coordinate system.
        # The "at" vector (0, 1, 0) indicates that the user's nose points along the y axis in the positive direction
        # The "up" vector (0, 0, 1) indicates that the z axis points straight upwards out the top of the user's head.
        self.listener.orientation = (0, 0, 1, 0, 1, 0)

        # Multiple sound sources are created that the system can rotate between for subsequent sound clips.
        # This allows overlapping sounds, but avoids bugs caused by too many source IDs
        # (eventually get the intractable "invalid ALC enum" error)
        # PLEASE NOTE: increase the number of sources (num_sources) if you are playing many sounds at once!
        num_sources = 10
        self.sources = []
        self.src_i = 0  # index of current source to be used
        for i in range(num_sources):
            self.sources.append(SoundSource())
            self.sources[i].looping = False

        # Load all sound clips in wav_files subdirectory into a dictionary, with file names as keys:
        self.clips = {}
        soundFiles = os.listdir('./audios')
        for fileName in soundFiles:
            print(fileName)
            self.clips[fileName] = load_wav_file(os.path.join('./audios', fileName))

    def play_sound(self, label="NOLABEL.wav", rho=0, theta=0, phi=0):
        if label in self.clips:
            self.sources[self.src_i].bufferqueue = []
            self.sources[self.src_i].position = self.universalCoords_to_openAL(rho, theta, phi);
            self.sources[self.src_i].queue(self.clips[label])
            self.sink.process_source(self.sources[self.src_i])
            self.sink.play(self.sources[self.src_i])
            # self.sink.update()
            self.rotate_source()
        else:
            print('ERROR: No sound clip named ' + label)

    def universalCoords_to_openAL(self, rho_univ, theta_univ, phi_univ):
        theta_rad = m.radians(theta_univ)  # convert to radians
        phi_rad = m.radians(phi_univ)

        x = rho_univ * m.cos(phi_rad) * m.cos(theta_rad)  # convert from spherical coordinates to x-y-z coordinates
        y = rho_univ * m.sin(phi_rad) 
        z = rho_univ * m.cos(phi_rad) * m.sin(theta_rad) 
        return (x, y, z)

    def rotate_source(self):
        if self.src_i == len(self.sources) - 1:
            self.src_i = 0
        else:
            self.src_i = self.src_i + 1