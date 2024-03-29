#using PyAL
import sys, os
#sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
from openal import al, alc

#imports for sound loading and wait during example
import wave
import time
import sys
import os

import ctypes

#For more information on HRTF tables, visit:
#http://recherche.ircam.fr/equipes/salles/listen/index.html


#load a listener to load and play sounds.
class Listener(object):
    def __init__(self):
    #load device/context/listener
        self.device = alc.alcOpenDevice(None)
        self.context = alc.alcCreateContext(self.device, None)
        alc.alcMakeContextCurrent(self.context)

    #get list of available htrf tables
        self.hrtf_buffers = [alc.ALCint(),alc.ALCint*4,alc.ALCint()]
        alc.alcGetIntegerv(self.device,alc.ALC_NUM_HRTF_SPECIFIERS_SOFT, 1,self.hrtf_buffers[0])

    #attributes for device to set specified hrtf table
        self.hrtf_select = self.hrtf_buffers[1](alc.ALC_HRTF_SOFT,alc.ALC_TRUE,alc.ALC_HRTF_ID_SOFT,1)


#list number of available hrtf tables
    def _hrtf_tables(self):
        return self.hrtf_buffers[0].value


#assign hrtf table to device and soft reboot to take effect
    def _set_hrtf(self,num):
        if num == None:
            alc.alcResetDeviceSOFT(self.device, None)
        elif num >= 0 and num <= self.hrtf_buffers[0].value:
            self.hrtf_select[3] = num
        #reset the device so the new hrtf settings take effect
            alc.alcResetDeviceSOFT(self.device, self.hrtf_select)


#confirm hrtf has been loaded and is enabled
    def _get_hrtf(self):
        alc.alcGetIntegerv(self.device,alc.ALC_HRTF_SOFT,1,self.hrtf_buffers[2])
        if self.hrtf_buffers[2].value == alc.ALC_HRTF_DISABLED_SOFT:
            return False
        elif self.hrtf_buffers[2].value == alc.ALC_HRTF_ENABLED_SOFT:
            return True
        elif self.hrtf_buffers[2].value == alc.ALC_HRTF_DENIED_SOFT:
            return False
        elif self.hrtf_buffers[2].value == alc.ALC_HRTF_REQUIRED_SOFT:
            return True
        elif self.hrtf_buffers[2].value == alc.ALC_HRTF_HEADPHONES_DETECTED_SOFT:
            return True
        elif self.hrtf_buffers[2].value == alc.ALC_HRTF_UNSUPPORTED_FORMAT_SOFT:
            return False


#set player position
    def _set_position(self,pos):
        self._position = pos
        x,y,z = map(int, pos)
        al.alListener3f(al.AL_POSITION, x, y, z)

    def _get_position(self):
        return self._position

#delete current listener
    def delete(self):
        alc.alcDestroyContext(self.context)
        alc.alcCloseDevice(self.device)

    position = property(_get_position, _set_position,doc="""get/set position""")
    hrtf = property(_get_hrtf, _set_hrtf,doc="""get status/set hrtf""")
    hrtf_tables = property(_hrtf_tables,None,doc="""get number of hrtf tables""")


#load and store a wav file into an openal buffer
class load_sound(object):
    def __init__(self,filename):
        self.name = filename

        wavefp = wave.open(filename)
        channels = wavefp.getnchannels()
        bitrate = wavefp.getsampwidth() * 8
        samplerate = wavefp.getframerate()
        wavbuf = wavefp.readframes(wavefp.getnframes())
        self.duration = (len(wavbuf) / float(samplerate))/2
        self.length = len(wavbuf)
        formatmap = {
            (1, 8) : al.AL_FORMAT_MONO8,
            (2, 8) : al.AL_FORMAT_STEREO8,
            (1, 16): al.AL_FORMAT_MONO16,
            (2, 16) : al.AL_FORMAT_STEREO16,
        }
        alformat = formatmap[(channels, bitrate)]

        self.buf = al.ALuint(0)
        al.alGenBuffers(1, self.buf)
    #allocate buffer space to: buffer, format, data, len(data), and samplerate
        al.alBufferData(self.buf, alformat, wavbuf, len(wavbuf), samplerate)

#delete loaded sound
    def delete(self):
        al.alDeleteBuffers(1, self.buf)



#load sound buffers into an openal source player to play them
class Player(object):
#load default settings
    def __init__(self):
    #load source player
        self.source = al.ALuint(0)
        al.alGenSources(1, self.source)
    #disable rolloff factor by default
        al.alSourcef(self.source, al.AL_ROLLOFF_FACTOR, 0)
    #disable source relative by default
        al.alSourcei(self.source, al.AL_SOURCE_RELATIVE,0)
    #capture player state buffer
        self.state = al.ALint(0)
    #set internal variable tracking
        self._volume = 1.0
        self._pitch = 1.0
        self._position = [0,0,0]
        self._rolloff = .1
        self._loop = False
        self.queue = []

#set rolloff factor, determines volume based on distance from listener
    def _set_rolloff(self,value):
        self._rolloff = value
        al.alSourcef(self.source, al.AL_ROLLOFF_FACTOR, value)

    def _get_rolloff(self):
        return self._rolloff


#set whether looping or not - true/false 1/0
    def _set_loop(self,lo):
        self._loop = lo
        al.alSourcei(self.source, al.AL_LOOPING, lo)

    def _get_loop(self):
        return self._loop
      

#set player position
    def _set_position(self,pos):
        self._position = pos
        x,y,z = map(int, pos)
        al.alSource3f(self.source, al.AL_POSITION, x, y, z)

    def _get_position(self):
        return self._position
        

#set pitch - 1.5-0.5 float range only
    def _set_pitch(self,pit):
        self._pitch = pit
        al.alSourcef(self.source, al.AL_PITCH, pit)

    def _get_pitch(self):
        return self._pitch

#set volume - 1.0 float range only
    def _set_volume(self,vol):
        self._volume = vol
        al.alSourcef(self.source, al.AL_GAIN, vol)

    def _get_volume(self):
        return self._volume

#queue a sound buffer
    def add(self,sound):
        al.alSourceQueueBuffers(self.source, 1, sound.buf) #self.buf
        self.queue.append(sound)

#remove a sound from the queue (detach & unqueue to properly remove)
    def remove(self):
        if len(self.queue) > 0:
            al.alSourceUnqueueBuffers(self.source, 1, self.queue[0].buf) #self.buf
            al.alSourcei(self.source, al.AL_BUFFER, 0)
            self.queue.pop(0)

#play sound source
    def play(self):
        al.alSourcePlay(self.source)

#get current playing state
    def playing(self):
        al.alGetSourcei(self.source, al.AL_SOURCE_STATE, self.state)
        if self.state.value == al.AL_PLAYING:
            return True
        else:
            return False

#stop playing sound
    def stop(self):
        al.alSourceStop(self.source)

#rewind player
    def rewind(self):
        al.alSourceRewind(self.source)

#pause player
    def pause(self):
        al.alSourcePause(self.source)

#delete sound source
    def delete(self):
        al.alDeleteSources(1, self.source)

#Go straight to a set point in the sound file
    def _set_seek(self,offset):#float 0.0-1.0
        al.alSourcei(self.source,al.AL_BYTE_OFFSET,int(self.queue[0].length * offset))

#returns current buffer length position (IE: 21000), so divide by the buffers self.length
    def _get_seek(self):#returns float 0.0-1.0
        al.alGetSourcei(self.source, al.AL_BYTE_OFFSET, self.state)
        return float(self.state.value)/float(self.queue[0].length)

    rolloff = property(_get_rolloff, _set_rolloff,doc="""get/set rolloff factor""")
    volume = property(_get_volume, _set_volume,doc="""get/set volume""")
    pitch = property(_get_pitch, _set_pitch, doc="""get/set pitch""")
    loop = property(_get_loop, _set_loop, doc="""get/set loop state""")
    position = property(_get_position, _set_position,doc="""get/set position""")
    seek = property(_get_seek, _set_seek, doc="""get/set the current play position""")