import aiohttp
import os

async def generate_speech(text: str) -> bytes:
    """Generate speech from text using Sesame TTS"""
    
    sesame_url = os.getenv("SESAME_TTS_API_URL")
    sesame_key = os.getenv("SESAME_API_KEY")
    
    if not sesame_url or not sesame_key:
        # Return empty bytes for development
        return b""
    
    try:
        async with aiohttp.ClientSession() as session:
            data = {
                'text': text,
                'voice': 'default',  # Adjust based on Sesame API options
                'format': 'mp3'
            }
            
            headers = {
                'Authorization': f'Bearer {sesame_key}',
                'Content-Type': 'application/json'
            }
            
            async with session.post(sesame_url, json=data, headers=headers) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"TTS API error: {response.status}")
                    
    except Exception as e:
        print(f"TTS Error: {e}")
        return b""
