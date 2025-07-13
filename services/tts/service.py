"""Main TTS service implementation."""
import logging
import torch
import asyncio
import os
from typing import Dict, List, Optional, Union, AsyncGenerator
from .models import Segment, VoiceProfile, TTSRequest
from .generator import Generator, load_csm_1b
from .audio_processing import enhance_audio_quality, remove_long_silences, audio_to_bytes
import queue
import threading

logger = logging.getLogger(__name__)

class StreamingTTSBuffer:
    """Buffer for streaming TTS generation"""
    
    def __init__(self, max_size: int = 10):
        self.text_queue = queue.Queue(maxsize=max_size)
        self.audio_queue = queue.Queue(maxsize=max_size)
        self.is_processing = False
        self.is_complete = False
    
    def add_text(self, text: str):
        """Add text to generation queue"""
        if text.strip():
            self.text_queue.put(text)
    
    def complete(self):
        """Mark text input as complete"""
        self.is_complete = True
        self.text_queue.put(None)  # Sentinel value
    
    def get_audio(self) -> Optional[bytes]:
        """Get generated audio chunk"""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None

class TTSService:
    """Main TTS service for local text-to-speech generation."""
    
    def __init__(self, model_path: str = None, device: str = None):
        """Initialize TTS service."""
        # Auto-detect device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.device = device
        self.generator = None
        self.sample_rate = 24000
        self.model_path = model_path
        
        # Voice mappings
        self.standard_voices = {
            "alloy": 0, "echo": 1, "fable": 2, 
            "onyx": 3, "nova": 4, "shimmer": 5
        }
        self.cloned_voices: Dict[str, VoiceProfile] = {}
        
        # Initialize generator
        self._initialize_generator()
        
        # Streaming parameters
        self.streaming_buffers: Dict[str, StreamingTTSBuffer] = {}
        
        logger.info(f"TTS Service initialized on {device}")
    
    def _initialize_generator(self):
        """Initialize the TTS generator."""
        try:
            if self.model_path and os.path.exists(self.model_path):
                self.generator = load_csm_1b(self.model_path, self.device)
            else:
                # Create a basic generator for testing
                self.generator = Generator(device=self.device)
            
            if hasattr(self.generator, 'sample_rate'):
                self.sample_rate = self.generator.sample_rate
                
            logger.info(f"Generator initialized with sample rate: {self.sample_rate}")
        except Exception as e:
            logger.error(f"Failed to initialize generator: {e}")
            self.generator = Generator(device=self.device)
    
    async def generate_speech(
        self, 
        text: str, 
        voice: str = "alloy",
        speed: float = 1.0,
        temperature: float = 0.7,
        response_format: str = "wav"
    ) -> bytes:
        """Generate speech from text."""
        if not self.generator:
            raise RuntimeError("TTS generator not initialized")
        
        # Map voice to speaker ID
        speaker_id = self._get_speaker_id(voice)
        
        try:
            # Run generation in thread pool to avoid blocking
            audio = await asyncio.get_event_loop().run_in_executor(
                None, 
                self._generate_audio,
                text, 
                speaker_id, 
                temperature
            )
            
            # Apply speed adjustment
            if speed != 1.0:
                audio = self._adjust_speed(audio, speed)
            
            # Apply audio enhancements
            audio = enhance_audio_quality(audio, self.sample_rate)
            audio = remove_long_silences(audio, self.sample_rate)
            
            # Convert to bytes
            audio_bytes = audio_to_bytes(audio, self.sample_rate, response_format)
            
            logger.info(f"Generated {len(audio_bytes)} bytes of audio for voice '{voice}'")
            return audio_bytes
            
        except Exception as e:
            logger.error(f"Speech generation failed: {e}")
            raise
    
    async def generate_speech_streaming(
        self, 
        session_id: str,
        voice: str = "alloy",
        speed: float = 1.0,
        temperature: float = 0.7,
        response_format: str = "wav"
    ) -> AsyncGenerator[bytes, None]:
        """Generate speech from streaming text input."""
        
        if session_id not in self.streaming_buffers:
            self.streaming_buffers[session_id] = StreamingTTSBuffer()
        
        buffer = self.streaming_buffers[session_id]
        speaker_id = self._get_speaker_id(voice)
        
        try:
            # Start background processing
            processing_task = asyncio.create_task(
                self._process_streaming_text(buffer, speaker_id, temperature, speed, response_format)
            )
            
            # Yield audio chunks as they become available
            while not (buffer.is_complete and buffer.text_queue.empty() and buffer.audio_queue.empty()):
                audio_chunk = buffer.get_audio()
                if audio_chunk:
                    yield audio_chunk
                else:
                    await asyncio.sleep(0.01)  # Small delay to prevent busy waiting
            
            # Wait for processing to complete
            await processing_task
            
            # Yield any remaining audio
            while True:
                audio_chunk = buffer.get_audio()
                if audio_chunk is None:
                    break
                yield audio_chunk
            
        finally:
            # Cleanup
            if session_id in self.streaming_buffers:
                del self.streaming_buffers[session_id]
    
    async def _process_streaming_text(
        self, 
        buffer: StreamingTTSBuffer, 
        speaker_id: int, 
        temperature: float,
        speed: float,
        response_format: str
    ):
        """Background task to process text chunks into audio"""
        
        while True:
            try:
                # Get text chunk
                text_chunk = buffer.text_queue.get(timeout=1.0)
                
                if text_chunk is None:  # Sentinel value
                    break
                
                # Generate audio for this chunk
                audio = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._generate_audio,
                    text_chunk,
                    speaker_id,
                    temperature
                )
                
                # Apply speed adjustment
                if speed != 1.0:
                    audio = self._adjust_speed(audio, speed)
                
                # Apply audio enhancements (lighter processing for streaming)
                audio = self._light_audio_processing(audio)
                
                # Convert to bytes
                audio_bytes = audio_to_bytes(audio, self.sample_rate, response_format)
                
                # Add to output queue
                buffer.audio_queue.put(audio_bytes)
                
            except queue.Empty:
                if buffer.is_complete:
                    break
                continue
            except Exception as e:
                logger.error(f"Streaming TTS processing error: {e}")
                break
    
    def _light_audio_processing(self, audio: torch.Tensor) -> torch.Tensor:
        """Lightweight audio processing for streaming"""
        # Apply minimal processing to reduce latency
        return audio
    
    def add_text_to_stream(self, session_id: str, text: str):
        """Add text to streaming TTS session"""
        if session_id in self.streaming_buffers:
            self.streaming_buffers[session_id].add_text(text)
    
    def complete_stream(self, session_id: str):
        """Mark streaming session as complete"""
        if session_id in self.streaming_buffers:
            self.streaming_buffers[session_id].complete()
    
    def _generate_audio(self, text: str, speaker_id: int, temperature: float) -> torch.Tensor:
        """Generate audio tensor from text."""
        return self.generator.generate(
            text=text,
            speaker=speaker_id,
            temperature=temperature,
            context=[]
        )
    
    def _get_speaker_id(self, voice: str) -> int:
        """Get speaker ID for voice name."""
        # Check standard voices
        if voice in self.standard_voices:
            return self.standard_voices[voice]
        
        # Check cloned voices
        if voice in self.cloned_voices:
            return self.cloned_voices[voice].speaker_id
        
        # Default to first speaker
        logger.warning(f"Unknown voice '{voice}', using default")
        return 0
    
    def _adjust_speed(self, audio: torch.Tensor, speed: float) -> torch.Tensor:
        """Adjust audio playback speed."""
        if speed == 1.0:
            return audio
        
        # Simple resampling for speed adjustment
        try:
            import torchaudio.functional as F
            new_sample_rate = int(self.sample_rate * speed)
            audio_resampled = F.resample(audio, self.sample_rate, new_sample_rate)
            return audio_resampled
        except ImportError:
            logger.warning("torchaudio not available for speed adjustment")
            return audio
    
    def list_voices(self) -> List[Dict[str, str]]:
        """List available voices."""
        voices = []
        
        # Add standard voices
        for voice_name, speaker_id in self.standard_voices.items():
            voices.append({
                "voice_id": voice_name,
                "name": voice_name.title(),
                "description": f"Standard voice {voice_name}",
                "type": "standard"
            })
        
        # Add cloned voices
        for voice_id, profile in self.cloned_voices.items():
            voices.append({
                "voice_id": voice_id,
                "name": profile.name,
                "description": profile.description or f"Cloned voice {profile.name}",
                "type": "cloned"
            })
        
        return voices
    
    def clone_voice(
        self, 
        name: str, 
        audio_data: bytes, 
        description: str = None
    ) -> str:
        """Clone a voice from audio data."""
        try:
            # Generate a unique voice ID
            voice_id = f"cloned_{len(self.cloned_voices)}_{name.lower().replace(' ', '_')}"
            
            # For now, assign to next available speaker ID
            speaker_id = len(self.standard_voices) + len(self.cloned_voices)
            
            # Create voice profile
            profile = VoiceProfile(
                id=voice_id,
                name=name,
                speaker_id=speaker_id,
                description=description or f"Cloned voice: {name}"
            )
            
            self.cloned_voices[voice_id] = profile
            
            logger.info(f"Cloned voice '{name}' with ID '{voice_id}'")
            return voice_id
            
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            raise
    
    def get_health_status(self) -> Dict:
        """Get service health status."""
        return {
            "status": "healthy" if self.generator else "unhealthy",
            "device": self.device,
            "sample_rate": self.sample_rate,
            "standard_voices": len(self.standard_voices),
            "cloned_voices": len(self.cloned_voices),
            "model_loaded": self.generator is not None
        }
