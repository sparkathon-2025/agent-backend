import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

async def generate_speech(text: str) -> bytes:
    """Generate speech from text using OpenAI TTS"""
    
    try:
        response = openai.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
            response_format="mp3"
        )
        
        return response.content
        
    except Exception as e:
        print(f"TTS Error: {e}")
        # Return empty bytes if TTS fails
        return b""
