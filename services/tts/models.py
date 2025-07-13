from dataclasses import dataclass
from typing import List, Tuple
import torch

@dataclass
class Segment:
    """A segment of speech with text, speaker, and audio."""
    speaker: int
    text: str
    # (num_samples,), sample_rate = 24_000
    audio: torch.Tensor

@dataclass
class VoiceProfile:
    """Voice profile for cloned voices."""
    id: str
    name: str
    speaker_id: int
    description: str = ""
    reference_audio: torch.Tensor = None
    
@dataclass
class TTSRequest:
    """TTS generation request."""
    text: str
    voice: str = "alloy"
    speed: float = 1.0
    temperature: float = 0.7
    response_format: str = "mp3"
    model: str = "csm-1b"
