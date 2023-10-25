import torch
import speech_recognition as sr
import math
import audioop
import collections

class CustomRecognizer(sr.Recognizer):
	# Special custom changes in this method
	def __init__(self):
		super().__init__()
		self.model, self.utils = torch.hub.load(repo_or_dir='./silero-vad',
												model='silero_vad',
												force_reload=True,
												source='local',
												onnx=False)
		# source.CHUNK = 1024 / source.SAMPLERATE
		self.seconds_per_buffer = float(1024) / 16000
		self.pause_buffer_count = int(math.ceil(self.pause_threshold / self.seconds_per_buffer))  # number of buffers of non-speaking audio during a phrase, before the phrase should be considered complete
		self.phrase_buffer_count = int(math.ceil(self.phrase_threshold / self.seconds_per_buffer))-2  # minimum number of buffers of speaking audio before we consider the speaking audio a phrase
		self.non_speaking_buffer_count = int(math.ceil(self.non_speaking_duration / self.seconds_per_buffer))  # maximum number of buffers of non-speaking audio to retain before and after a phrase
		self.mean_noise = 0
		self.num_samples = 0
		self.mean_sum = 0
		self.rms_flag = True

	def listen(self, source, phrase_time_limit=2):
		"""
		Records a single phrase from ``source`` (an ``AudioSource`` instance) into an ``AudioData`` instance, which it returns.

		This is done by waiting until the audio has an energy above ``recognizer_instance.energy_threshold`` (the user has started speaking), and then recording until it encounters ``recognizer_instance.pause_threshold`` seconds of non-speaking or there is no more audio input. The ending silence is not included.

		The ``timeout`` parameter is the maximum number of seconds that this will wait for a phrase to start before giving up and throwing an ``speech_recognition.WaitTimeoutError`` exception. If ``timeout`` is ``None``, there will be no wait timeout.

		The ``phrase_time_limit`` parameter is the maximum number of seconds that this will allow a phrase to continue before stopping and returning the part of the phrase processed before the time limit was reached. The resulting audio will be the phrase cut off at the time limit. If ``phrase_timeout`` is ``None``, there will be no phrase time limit.

		The ``snowboy_configuration`` parameter allows integration with `Snowboy <https://snowboy.kitt.ai/>`__, an offline, high-accuracy, power-efficient hotword recognition engine. When used, this function will pause until Snowboy detects a hotword, after which it will unpause. This parameter should either be ``None`` to turn off Snowboy support, or a tuple of the form ``(SNOWBOY_LOCATION, LIST_OF_HOT_WORD_FILES)``, where ``SNOWBOY_LOCATION`` is the path to the Snowboy root directory, and ``LIST_OF_HOT_WORD_FILES`` is a list of paths to Snowboy hotword configuration files (`*.pmdl` or `*.umdl` format).

		This operation will always complete within ``timeout + phrase_timeout`` seconds if both are numbers, either by returning the audio data, or by raising a ``speech_recognition.WaitTimeoutError`` exception.
		"""
		
		print("pause", self.pause_buffer_count,"phrase buffer", self.phrase_buffer_count, "nonspeaking", self.non_speaking_buffer_count )
		# read audio input for phrases until there is a phrase that is long enough
		elapsed_time = 0  # number of seconds of audio read
		buffer = b""  # an empty buffer means that the stream has ended and there is no data left to read


		while True:
			frames = collections.deque()
			
			while True:
				
				# handle waiting too long for phrase by raising an exception
				elapsed_time += self.seconds_per_buffer

				buffer = source.stream.read(source.CHUNK)
				#tensor_buffer = torch.from_numpy(np.frombuffer(buffer, np.int16).flatten().astype(np.float32) / 32768.0)
				tensor_buffer = torch.frombuffer(buffer, dtype=torch.int16).float() / 32768.0
				

				frames.append(tensor_buffer)
				if len(frames) > self.non_speaking_buffer_count:  # ensure we only keep the needed amount of non-speaking buffers
					frames.popleft()

				# detect whether speaking has started on audio input
				prob = self.model(tensor_buffer, 16000).item()
				energy = audioop.rms(buffer, source.SAMPLE_WIDTH)
				#print(source.SAMPLE_WIDTH)
				if prob > self.energy_threshold and energy > 900: 
					break

			# read audio input until the phrase ends
			pause_count, phrase_count = 0, 0
			phrase_start_time = elapsed_time
			while True:
				# handle phrase being too long by cutting off the audio
				elapsed_time += self.seconds_per_buffer
				if phrase_time_limit and elapsed_time - phrase_start_time > phrase_time_limit:
					return []

				buffer = source.stream.read(source.CHUNK)
				#tensor_buffer = torch.from_numpy(np.frombuffer(buffer, np.int16).flatten().astype(np.float32) / 32768.0)
				tensor_buffer = torch.frombuffer(buffer, dtype=torch.int16).float() / 32768.0

				frames.append(tensor_buffer)
				phrase_count += 1

				# check if speaking has stopped for longer than the pause threshold on the audio input
				energy = self.model(tensor_buffer, 16000).item()

				if energy > self.energy_threshold:
					pause_count = 0
				else:
					pause_count += 1
				if pause_count > self.pause_buffer_count:  # end of the phrase
					break

			# check how long the detected phrase is, and retry listening if the phrase is too short
			phrase_count -= pause_count  # exclude the buffers for the pause before the phrase
			if phrase_count >= self.phrase_buffer_count or len(buffer) == 0: break  # phrase is long enough or we've reached the end of the stream, so stop listening

		# obtain frame data
		for i in range(pause_count - self.non_speaking_buffer_count): frames.pop()  # remove extra non-speaking frames at the end
		
		return frames