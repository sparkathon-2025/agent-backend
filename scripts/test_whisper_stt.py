"""
Script to record audio from microphone and transcribe using WhisperSTT service.
Usage:
    python scripts/test_whisper_stt.py
"""
import asyncio
import io
import wave

import pyaudio

# Ensure project root is in path for module imports
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.whisper_stt import transcribe_audio

# Audio recording parameters
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK = 1024
FORMAT = pyaudio.paInt16
RECORD_SECONDS = 5  # seconds to record


def record_audio(duration=RECORD_SECONDS) -> bytes:
    """Record audio from default microphone and return WAV data as bytes."""
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
    print(f"Recording for {duration} seconds...")
    frames = []
    for _ in range(0, int(SAMPLE_RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Recording complete.")
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Write WAV header into BytesIO
    buffer = io.BytesIO()
    wf = wave.open(buffer, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    return buffer.getvalue()


async def main():
    # Record audio
    wav_bytes = record_audio()

    # Transcribe audio using WhisperSTT
    print("Transcribing audio...")
    text = await transcribe_audio(wav_bytes)
    print(f"Transcription: {text}")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user.")
