import queue
import threading
import whisper
import soundfile as sf
import numpy as np
import torch
import speech_recognition as sr
import matplotlib.pyplot as plt

def save_audio(audio_queue):
    # create a new thread to save audio data to WAV file
    counter = 0
    while True:
        try:
            audio_data = audio_queue.get(timeout=1)
            filename = f"audio_{counter}.wav"
            sf.write(filename, audio_data.numpy(), 16000, 'PCM_16')
            counter += 1
        except queue.Empty:
            continue


def transcribe_forever(audio_queue, result_queue, audio_model):

    cont = 0
    while True:
        cont+=1
        print("transcribe")
        audio_data = audio_queue.get()

        time_axis = np.arange(len(audio_data)) / 16000



        result = audio_model.transcribe(audio_data.numpy(), language='english')

        speech = result["text"]
        # plot the waveform
        plt.clf()
        plt.plot(time_axis, audio_data)
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")
        plt.title(speech)
        plt.ion()
        plt.pause(.2)
        plt.savefig(f'audio_signal{cont}.png')
        result_queue.put_nowait(speech)


def record_audio(audio_queue, energy=360, pause=0.55, dynamic_energy=False):
    # load the speech recognizer and set the initial energy threshold and pause threshold
    r = sr.Recognizer()
    r.energy_threshold = energy
    r.pause_threshold = pause
    r.dynamic_energy_threshold = dynamic_energy

    with sr.Microphone(sample_rate=16000) as source:
        print("Say something!")
        i = 0
        while True:
            # get audio data from the microphone
            r.adjust_for_ambient_noise(source, duration=.22)
            audio = r.listen(source)
            torch_audio = torch.from_numpy(
                np.frombuffer(audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0)
            audio_data = torch_audio
            # create a time axis

            print(np.std(audio_data.numpy()),len(audio_data))
            
            audio_queue.put_nowait(audio_data)
            i += 1


if __name__ == "__main__":
    audio_queue = queue.Queue()
    result_queue = queue.Queue()

    whisper_audio_model = whisper.load_model("base")

    transcribe_thread = threading.Thread(target=transcribe_forever, args=(audio_queue, result_queue, whisper_audio_model), daemon=True)
    transcribe_thread.start()

    record_thread = threading.Thread(target=record_audio, args=(audio_queue,), daemon=True)
    record_thread.start()

    while True:
        speech = result_queue.get()
        print(speech)
