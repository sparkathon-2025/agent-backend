import logging
import os
from typing import Optional, AsyncGenerator
from .tts.service import TTSService

logger = logging.getLogger(__name__)

# Global TTS service instance
_tts_service: Optional[TTSService] = None

def get_tts_service() -> TTSService:
    """Get or create TTS service instance."""
    global _tts_service
    
    if _tts_service is None:
        # Initialize TTS service
        model_path = os.getenv("TTS_MODEL_PATH")
        device = os.getenv("TTS_DEVICE", "cpu")
        
        logger.info(f"Initializing local TTS service (device: {device})")
        _tts_service = TTSService(model_path=model_path, device=device)
    
    return _tts_service

async def generate_speech(
    text: str, 
    voice: str = "alloy",
    response_format: str = "mp3",
    speed: float = 1.0
) -> bytes:
    """Generate speech from text using local TTS service"""
    
    try:
        tts_service = get_tts_service()
        
        logger.info(f"Generating TTS for text length: {len(text)}, voice: {voice}")
        
        audio_data = await tts_service.generate_speech(
            text=text,
            voice=voice,
            speed=speed,
            response_format=response_format
        )
        
        logger.info(f"Successfully generated {len(audio_data)} bytes of audio")
        return audio_data
        
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        return b""

async def list_available_voices() -> list:
    """Get list of available voices from local TTS service"""
    
    try:
        tts_service = get_tts_service()
        voices = tts_service.list_voices()
        return voices
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        return []

async def clone_voice_from_audio(
    voice_name: str,
    audio_data: bytes,
    transcript: str = None,
    description: str = None
) -> dict:
    """Clone a voice from audio data using local TTS service"""
    
    try:
        tts_service = get_tts_service()
        
        voice_id = tts_service.clone_voice(
            name=voice_name,
            audio_data=audio_data,
            description=description
        )
        
        result = {
            "voice_id": voice_id,
            "name": voice_name,
            "description": description,
            "status": "success"
        }
        
        logger.info(f"Successfully cloned voice: {voice_name}")
        return result
        
    except Exception as e:
        logger.error(f"Voice cloning error: {e}")
        return {"status": "error", "message": str(e)}

async def generate_speech_with_cloned_voice(
    text: str,
    voice_id: str,
    temperature: float = 0.7
) -> bytes:
    """Generate speech using a cloned voice"""
    
    try:
        tts_service = get_tts_service()
        
        audio_data = await tts_service.generate_speech(
            text=text,
            voice=voice_id,
            temperature=temperature
        )
        
        logger.info(f"Generated speech with cloned voice {voice_id}")
        return audio_data
        
    except Exception as e:
        logger.error(f"Cloned voice TTS error: {e}")
        # Fallback to regular TTS with the voice_id as voice name
        return await generate_speech(text, voice=voice_id)

async def get_tts_health() -> dict:
    """Get TTS service health status"""
    
    try:
        tts_service = get_tts_service()
        return tts_service.get_health_status()
    except Exception as e:
        logger.error(f"Error getting TTS health: {e}")
        return {"status": "error", "message": str(e)}

async def generate_speech_streaming(
    session_id: str,
    voice: str = "alloy",
    response_format: str = "mp3",
    speed: float = 1.0
) -> AsyncGenerator[bytes, None]:
    """Generate speech from streaming text input"""
    
    try:
        tts_service = get_tts_service()
        
        logger.info(f"Starting streaming TTS session: {session_id}, voice: {voice}")
        
        async for audio_chunk in tts_service.generate_speech_streaming(
            session_id=session_id,
            voice=voice,
            speed=speed,
            response_format=response_format
        ):
            yield audio_chunk
            
    except Exception as e:
        logger.error(f"Streaming TTS Error: {e}")
        yield b""

def add_text_to_stream(session_id: str, text: str):
    """Add text to streaming TTS session"""
    try:
        tts_service = get_tts_service()
        tts_service.add_text_to_stream(session_id, text)
        logger.debug(f"Added text to stream {session_id}: {text[:50]}...")
    except Exception as e:
        logger.error(f"Error adding text to stream: {e}")

def complete_stream(session_id: str):
    """Mark streaming session as complete"""
    try:
        tts_service = get_tts_service()
        tts_service.complete_stream(session_id)
        logger.info(f"Completed stream {session_id}")
    except Exception as e:
        logger.error(f"Error completing stream: {e}")
