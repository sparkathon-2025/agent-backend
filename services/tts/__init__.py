"""
TTS (Text-to-Speech) service module.
Provides local TTS capabilities using CSM-1B and Dia models.
"""

from .service import TTSService
from .models import Segment
from .generator import Generator, load_csm_1b

__all__ = ['TTSService', 'Segment', 'Generator', 'load_csm_1b']
