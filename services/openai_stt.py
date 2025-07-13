import openai
import os
import io

openai.api_key = os.getenv("OPENAI_API_KEY")

async def transcribe_audio(audio_data: bytes) -> str:
    """Transcribe audio using OpenAI Whisper"""
    
    if not openai.api_key:
        # Fallback for development
        return "This is a sample transcription for development"
    
    try:
        # Create a file-like object from bytes
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.wav"  # Whisper needs a filename
        
        response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
        
        return response if isinstance(response, str) else response.text
        
    except Exception as e:
        print(f"STT Error: {e}")
        return "Sorry, I couldn't understand what you said."
