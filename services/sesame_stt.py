import aiohttp
import os

async def transcribe_audio(audio_data: bytes) -> str:
    """Transcribe audio using Sesame CSM"""
    
    sesame_url = os.getenv("SESAME_API_URL")
    sesame_key = os.getenv("SESAME_API_KEY")
    
    if not sesame_url or not sesame_key:
        # Fallback for development
        return "This is a sample transcription for development"
    
    try:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('audio', audio_data, content_type='audio/wav')
            
            headers = {
                'Authorization': f'Bearer {sesame_key}'
            }
            
            async with session.post(sesame_url, data=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('transcription', 'Could not transcribe audio')
                else:
                    raise Exception(f"STT API error: {response.status}")
                    
    except Exception as e:
        print(f"STT Error: {e}")
        return "Sorry, I couldn't understand what you said."
