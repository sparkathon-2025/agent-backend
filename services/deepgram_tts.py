import logging
import os
import asyncio
from typing import Optional, AsyncGenerator, List, Dict
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    SpeakOptions,
    SpeakWebSocketEvents,
    SpeakWSOptions,
)
import uuid
import io

logger = logging.getLogger(__name__)

# Global Deepgram client
_deepgram_client: Optional[DeepgramClient] = None
_active_streams: Dict[str, any] = {}

def get_deepgram_client() -> DeepgramClient:
    """Get or create Deepgram client instance."""
    global _deepgram_client
    
    if _deepgram_client is None:
        api_key = os.getenv("DEEPGRAM_API_KEY")
        if not api_key:
            raise ValueError("DEEPGRAM_API_KEY environment variable is required")
        
        config = DeepgramClientOptions()
        _deepgram_client = DeepgramClient(api_key, config)
        logger.info("Deepgram TTS client initialized")
    
    return _deepgram_client

async def generate_speech(
    text: str, 
    voice: str = "aura-2-thalia-en",
    response_format: str = "mp3",
    speed: float = 1.0
) -> bytes:
    """Generate speech from text using Deepgram TTS."""
    
    try:
        client = get_deepgram_client()
        
        # Map voice names to Deepgram models
        voice_mapping = {
            "alloy": "aura-2-thalia-en",
            "echo": "aura-2-luna-en", 
            "fable": "aura-2-stella-en",
            "onyx": "aura-2-arcas-en",
            "nova": "aura-2-thalia-en",
            "shimmer": "aura-2-hera-en"
        }
        
        model = voice_mapping.get(voice, voice)
        
        # Configure options
        options = SpeakOptions(
            model=model,
            encoding="mp3" if response_format == "mp3" else "wav",
        )
        
        # Generate speech
        response = await client.speak.asyncrest.v("1").stream_memory(
            {"text": text}, options
        )
        
        # Get audio bytes
        audio_data = response.stream_memory.getvalue()
        
        logger.info(f"Generated {len(audio_data)} bytes of audio for text: {text[:50]}...")
        return audio_data
        
    except Exception as e:
        logger.error(f"Deepgram TTS Error: {e}")
        return b""

async def list_available_voices() -> List[Dict]:
    """Get list of available voices from Deepgram."""
    
    voices = [
        {"voice_id": "alloy", "name": "Alloy", "description": "Neutral, balanced voice", "type": "standard"},
        {"voice_id": "echo", "name": "Echo", "description": "Clear, articulate voice", "type": "standard"},
        {"voice_id": "fable", "name": "Fable", "description": "Warm, storytelling voice", "type": "standard"},
        {"voice_id": "onyx", "name": "Onyx", "description": "Deep, authoritative voice", "type": "standard"},
        {"voice_id": "nova", "name": "Nova", "description": "Bright, energetic voice", "type": "standard"},
        {"voice_id": "shimmer", "name": "Shimmer", "description": "Gentle, soothing voice", "type": "standard"},
        {"voice_id": "aura-2-thalia-en", "name": "Thalia", "description": "Deepgram Aura Thalia", "type": "deepgram"},
        {"voice_id": "aura-2-luna-en", "name": "Luna", "description": "Deepgram Aura Luna", "type": "deepgram"},
        {"voice_id": "aura-2-stella-en", "name": "Stella", "description": "Deepgram Aura Stella", "type": "deepgram"},
        {"voice_id": "aura-2-arcas-en", "name": "Arcas", "description": "Deepgram Aura Arcas", "type": "deepgram"},
        {"voice_id": "aura-2-hera-en", "name": "Hera", "description": "Deepgram Aura Hera", "type": "deepgram"},
    ]
    
    return voices

class StreamingTTSSession:
    """Handles streaming TTS session with Deepgram WebSocket."""
    
    def __init__(self, session_id: str, voice: str = "aura-2-thalia-en"):
        self.session_id = session_id
        self.voice = voice
        self.connection = None
        self.audio_queue = asyncio.Queue()
        self.is_connected = False
        self.is_finished = False
        
    async def start(self):
        """Start the streaming TTS session."""
        try:
            client = get_deepgram_client()
            self.connection = client.speak.websocket.v("1")
            
            # Set up event handlers
            self.connection.on(SpeakWebSocketEvents.Open, self._on_open)
            self.connection.on(SpeakWebSocketEvents.AudioData, self._on_audio_data)
            self.connection.on(SpeakWebSocketEvents.Close, self._on_close)
            
            # Configure options
            voice_mapping = {
                "alloy": "aura-2-thalia-en",
                "echo": "aura-2-luna-en", 
                "fable": "aura-2-stella-en",
                "onyx": "aura-2-arcas-en",
                "nova": "aura-2-thalia-en",
                "shimmer": "aura-2-hera-en"
            }
            
            model = voice_mapping.get(self.voice, self.voice)
            
            options = SpeakWSOptions(
                model=model,
                encoding="linear16",
                sample_rate=16000,
            )
            
            # Start connection
            if self.connection.start(options):
                self.is_connected = True
                logger.info(f"Started streaming TTS session: {self.session_id}")
            else:
                raise Exception("Failed to start Deepgram TTS connection")
                
        except Exception as e:
            logger.error(f"Failed to start streaming TTS session: {e}")
            raise
    
    def _on_open(self, open, **kwargs):
        """Handle WebSocket open event."""
        logger.debug(f"TTS WebSocket opened for session {self.session_id}")
    
    def _on_audio_data(self, data, **kwargs):
        """Handle incoming audio data."""
        try:
            self.audio_queue.put_nowait(data)
        except Exception as e:
            logger.error(f"Error queuing audio data: {e}")
    
    def _on_close(self, close, **kwargs):
        """Handle WebSocket close event."""
        logger.debug(f"TTS WebSocket closed for session {self.session_id}")
        self.is_connected = False
    
    async def send_text(self, text: str):
        """Send text to be converted to speech."""
        if self.connection and self.is_connected:
            self.connection.send_text(text)
    
    async def flush(self):
        """Flush the connection."""
        if self.connection and self.is_connected:
            self.connection.flush()
    
    async def finish(self):
        """Finish the session."""
        if self.connection and self.is_connected:
            self.connection.finish()
            self.is_finished = True
    
    async def get_audio_chunk(self) -> Optional[bytes]:
        """Get next audio chunk."""
        try:
            # Wait for audio with timeout
            return await asyncio.wait_for(self.audio_queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
            return None

async def generate_speech_streaming(
    session_id: str,
    voice: str = "alloy",
    response_format: str = "mp3",
    speed: float = 1.0
) -> AsyncGenerator[bytes, None]:
    """Generate speech from streaming text input using Deepgram WebSocket."""
    
    global _active_streams
    
    try:
        # Create streaming session
        session = StreamingTTSSession(session_id, voice)
        _active_streams[session_id] = session
        
        # Start the session
        await session.start()
        
        # Yield audio chunks as they arrive
        while not session.is_finished:
            audio_chunk = await session.get_audio_chunk()
            if audio_chunk:
                yield audio_chunk
            elif session.is_finished:
                break
        
        # Get any remaining audio
        while True:
            audio_chunk = await session.get_audio_chunk()
            if audio_chunk is None:
                break
            yield audio_chunk
            
    except Exception as e:
        logger.error(f"Streaming TTS error: {e}")
        yield b""
    finally:
        # Cleanup
        if session_id in _active_streams:
            del _active_streams[session_id]

def add_text_to_stream(session_id: str, text: str):
    """Add text to streaming TTS session."""
    try:
        if session_id in _active_streams:
            session = _active_streams[session_id]
            asyncio.create_task(session.send_text(text))
            logger.debug(f"Added text to stream {session_id}: {text[:50]}...")
    except Exception as e:
        logger.error(f"Error adding text to stream: {e}")

def complete_stream(session_id: str):
    """Mark streaming session as complete."""
    try:
        if session_id in _active_streams:
            session = _active_streams[session_id]
            asyncio.create_task(session.flush())
            asyncio.create_task(session.finish())
            logger.info(f"Completed stream {session_id}")
    except Exception as e:
        logger.error(f"Error completing stream: {e}")

async def get_tts_health() -> Dict:
    """Get TTS service health status."""
    try:
        # Test basic functionality
        test_audio = await generate_speech("Health check", "alloy")
        
        return {
            "status": "healthy" if test_audio else "unhealthy",
            "service": "deepgram",
            "voices_available": len(await list_available_voices()),
            "api_key_configured": bool(os.getenv("DEEPGRAM_API_KEY"))
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "deepgram", 
            "error": str(e),
            "api_key_configured": bool(os.getenv("DEEPGRAM_API_KEY"))
        }

# Legacy compatibility functions
async def clone_voice_from_audio(
    voice_name: str,
    audio_data: bytes,
    transcript: str = None,
    description: str = None
) -> Dict:
    """Voice cloning not supported by Deepgram - return error."""
    return {
        "status": "error", 
        "message": "Voice cloning not supported by Deepgram TTS"
    }

async def generate_speech_with_cloned_voice(
    text: str,
    voice_id: str,
    temperature: float = 0.7
) -> bytes:
    """Generate speech with cloned voice - fallback to regular TTS."""
    logger.warning(f"Cloned voice {voice_id} not supported, using regular TTS")
    return await generate_speech(text, voice=voice_id)
