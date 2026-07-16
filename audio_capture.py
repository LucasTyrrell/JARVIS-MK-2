import numpy as np
import pyaudio
from silero_vad import load_silero_vad, VADIterator
from elevenlabs_audio_generation import *
import shared_state
from shared_state import voice_detected


FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
FRAMES_PER_BUFFER = 512

audio = pyaudio.PyAudio()
user_is_speaking = False

stream = audio.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=FRAMES_PER_BUFFER)

def get_next_audio_frame(stream):
    data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
    audio_data = np.frombuffer(data, dtype=np.int16)
    return audio_data.astype(np.float32) / 32768.0 #puts it in the format silero expects


#VAD model setup

model = load_silero_vad()
vad_iteratior = VADIterator(
    model,
    sampling_rate=RATE,
    threshold=0.2,
    min_silence_duration_ms=700,
    speech_pad_ms=200
)



def VAD():
    global RATE, user_is_speaking
    chunk = get_next_audio_frame(stream)

    if user_is_speaking:
        shared_state.audio_buffer.append(chunk)

    result = vad_iteratior(chunk, return_seconds=False)

    if result is not None:
        if "start" in result:
            user_is_speaking = True
            shared_state.audio_buffer = [chunk]
        elif "end" in result:
            user_is_speaking = False
            full_speach = np.concatenate(shared_state.audio_buffer) if shared_state.audio_buffer else np.array([])
            shared_state.audio_buffer = []
            shared_state.current_query = "e
