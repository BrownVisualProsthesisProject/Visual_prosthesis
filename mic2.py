import pyaudio

p = pyaudio.PyAudio()
device_count = p.get_device_count()
for i in range(device_count):
    print(p.get_device_info_by_index(i))
