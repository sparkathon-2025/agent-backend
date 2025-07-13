"""Audio processing utilities for TTS."""
import logging
import numpy as np
import torch
import io
import wave

logger = logging.getLogger(__name__)

def remove_long_silences(
    audio: torch.Tensor, 
    sample_rate: int,
    min_speech_energy: float = 0.015,
    max_silence_sec: float = 0.4,
    keep_silence_sec: float = 0.1,
) -> torch.Tensor:
    """Remove uncomfortably long silences from audio while preserving natural pauses."""
    # ...existing code from original implementation...
    audio_np = audio.cpu().numpy()
    
    frame_size = int(0.02 * sample_rate)  # 20ms frames
    hop_length = int(0.01 * sample_rate)  # 10ms hop
    
    frames = []
    for i in range(0, len(audio_np) - frame_size + 1, hop_length):
        frames.append(audio_np[i:i+frame_size])
    
    if len(frames) < 2:
        return audio
        
    frames = np.array(frames)
    frame_energy = np.sqrt(np.mean(frames**2, axis=1))
    
    energy_threshold = max(min_speech_energy, np.percentile(frame_energy, 10))
    is_speech = frame_energy > energy_threshold
    
    speech_segments = []
    in_speech = False
    speech_start = 0
    
    for i in range(len(is_speech)):
        if is_speech[i] and not in_speech:
            in_speech = True
            speech_start = max(0, i * hop_length - int(keep_silence_sec * sample_rate))
        elif not is_speech[i] and in_speech:
            silence_length = 0
            for j in range(i, min(len(is_speech), i + int(max_silence_sec * sample_rate / hop_length))):
                if not is_speech[j]:
                    silence_length += 1
                else:
                    break
                    
            if silence_length * hop_length >= max_silence_sec * sample_rate:
                in_speech = False
                speech_end = min(len(audio_np), i * hop_length + int(keep_silence_sec * sample_rate))
                speech_segments.append((speech_start, speech_end))
    
    if in_speech:
        speech_segments.append((speech_start, len(audio_np)))
    
    if not speech_segments:
        logger.warning("No speech segments detected, returning original audio")
        return audio
    
    result = []
    
    if speech_segments[0][0] > 0:
        silence_samples = min(int(0.1 * sample_rate), speech_segments[0][0])
        if silence_samples > 0:
            result.append(audio_np[speech_segments[0][0] - silence_samples:speech_segments[0][0]])
    
    for i, (start, end) in enumerate(speech_segments):
        result.append(audio_np[start:end])
        
        if i < len(speech_segments) - 1:
            next_start = speech_segments[i+1][0]
            available_silence = next_start - end
            
            if available_silence > 0:
                silence_duration = min(available_silence, int(max_silence_sec * sample_rate))
                result.append(audio_np[end:end + silence_duration])
    
    processed_audio = np.concatenate(result)
    
    original_duration = len(audio_np) / sample_rate
    processed_duration = len(processed_audio) / sample_rate
    logger.info(f"Silence removal: {original_duration:.2f}s -> {processed_duration:.2f}s")
    
    return torch.tensor(processed_audio, device=audio.device, dtype=audio.dtype)

def enhance_audio_quality(audio: torch.Tensor, sample_rate: int) -> torch.Tensor:
    """Enhance audio quality by applying various processing techniques."""
    try:
        audio_np = audio.cpu().numpy()
        
        # Remove DC offset
        audio_np = audio_np - np.mean(audio_np)
        
        # Simple compression
        threshold = 0.5
        ratio = 1.5
        
        gain = np.ones_like(audio_np)
        for i in range(1, len(audio_np)):
            level = abs(audio_np[i])
            if level > threshold:
                gain[i] = threshold + (level - threshold) / ratio
                gain[i] = gain[i] / level if level > 0 else 1.0
            else:
                gain[i] = 1.0
            
            gain[i] = gain[i-1] + (gain[i] - gain[i-1]) * 0.01
        
        audio_np = audio_np * gain
        
        # Normalize
        max_val = np.max(np.abs(audio_np))
        if max_val > 0:
            audio_np = audio_np * 0.95 / max_val
        
        return torch.tensor(audio_np, device=audio.device, dtype=audio.dtype)
        
    except Exception as e:
        logger.warning(f"Audio quality enhancement failed: {e}")
        return audio

def audio_to_bytes(audio: torch.Tensor, sample_rate: int, format: str = "wav") -> bytes:
    """Convert audio tensor to bytes in specified format."""
    audio_np = audio.cpu().numpy()
    
    # Normalize to 16-bit range
    audio_np = np.clip(audio_np, -1.0, 1.0)
    audio_16bit = (audio_np * 32767).astype(np.int16)
    
    if format.lower() == "wav":
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_16bit.tobytes())
        return buffer.getvalue()
    else:
        # For other formats, you'd need additional libraries like pydub
        # For now, fallback to WAV
        return audio_to_bytes(audio, sample_rate, "wav")
