"""Main TTS service implementation."""
import logging
import torch
import asyncio
import os
from typing import Dict, List, Optional, Union
from .models import Segment, VoiceProfile, TTSRequest
from .generator import Generator, load_csm_1b
from .audio_processing import enhance_audio_quality, remove_long_silences, audio_to_bytes

logger = logging.getLogger(__name__)

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
