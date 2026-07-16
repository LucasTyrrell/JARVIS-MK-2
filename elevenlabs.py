from dotenv import load_dotenv
import threading
import pyaudio
import io
import os
import soundfile as sf
import elevenlabs
from elevenlabs.client import ElevenLabs
from time import sleep
from shared_state import bot_is_speaking, audio_queue, response_in_progress

p = pyaudio.PyAudio()

output_stream = p.open(
    format=p.get_format_from_width(2),
    channels=1,
    rate=16000,
    output=True,
)

load_dotenv()


def convert_text_to_speech(text, voice_id):
    elevenlabs = ElevenLabs(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
    )
    audio = elevenlabs.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id="eleven_v3",
        output_format="pcm_16000",
    )
    pcm_bytes = b"".join(audio)
    audio_queue.put(pcm_bytes)

def play_audio():
    while True:
        pcm_bytes = audio_queue.get()
        sleep(0.25)
        chunk_size = 4096
        for i in range(0, len(pcm_bytes), chunk_size):
            output_stream.write(pcm_bytes[i : i + chunk_size])


        if audio_queue.empty() and not response_in_progress:
            bot_is_speaking.clear()


threading.Thread(target=play_audio, daemon=True).start()

def convert_speech_to_text(audio, sample_rate):
    buffer = io.BytesIO()
    sf.write(buffer, audio, sample_rate, format="WAV")
    buffer.seek(0)

    elevenlabs = ElevenLabs(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
    )

    transcription = elevenlabs.speech_to_text.convert(
        file=buffer,
        model_id="scribe_v2",  # Model to use
        tag_audio_events=True,  # Tag audio events like laughter, applause, etc.
        language_code="eng",
        # Language of the audio file. If set to None, the model will detect the language automatically.
        diarize=True,  # Whether to annotate who is speaking
    )
    return transcription.text