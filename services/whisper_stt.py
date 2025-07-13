import torch
import torchaudio
import io
import tempfile
import os
import asyncio
import numpy as np
from collections import deque
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

class WhisperSTT:
    def __init__(self):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self.model_id = "openai/whisper-large-v3-turbo"
        
        # Initialize model and processor
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            self.model_id,
            torch_dtype=self.torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True
        )
        self.model.to(self.device)
        
        self.processor = AutoProcessor.from_pretrained(self.model_id)
        
        # Create pipeline
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
            torch_dtype=self.torch_dtype,
            device=self.device,
        )
        
        # Streaming parameters
        self.sample_rate = 16000
        self.chunk_duration = 1.0  # seconds
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
        self.buffer_duration = 3.0  # seconds of audio to keep in buffer
        self.buffer_size = int(self.sample_rate * self.buffer_duration)

class AudioBuffer:
    """Circular buffer for real-time audio processing"""
    
    def __init__(self, sample_rate: int, buffer_duration: float = 3.0):
        self.sample_rate = sample_rate
        self.buffer_size = int(sample_rate * buffer_duration)
        self.buffer = deque(maxlen=self.buffer_size)
        self.chunk_size = int(sample_rate * 1.0)  # 1 second chunks
        
    def add_audio(self, audio_data: np.ndarray):
        """Add audio data to buffer"""
        self.buffer.extend(audio_data)
    
    def get_chunk(self) -> np.ndarray:
        """Get audio chunk for processing"""
        if len(self.buffer) >= self.chunk_size:
            chunk = np.array(list(self.buffer)[-self.chunk_size:])
            return chunk
        return None
    
    def get_full_buffer(self) -> np.ndarray:
        """Get full buffer content"""
        return np.array(list(self.buffer)) if self.buffer else np.array([])

class StreamingSTT:
    """Streaming Speech-to-Text processor"""
    
    def __init__(self, whisper_stt: WhisperSTT):
        self.whisper = whisper_stt
        self.audio_buffer = AudioBuffer(whisper_stt.sample_rate)
        self.is_processing = False
        self.last_transcription = ""
        self.partial_transcripts = deque(maxlen=5)
        
    async def process_audio_chunk(self, audio_data: bytes) -> tuple[str, bool]:
        """
        Process audio chunk and return (transcription, is_final)
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.float32)
            
            # Add to buffer
            self.audio_buffer.add_audio(audio_array)
            
            # Get chunk for processing
            chunk = self.audio_buffer.get_chunk()
            if chunk is None:
                return "", False
            
            # Process chunk
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                # Convert to audio file
                torchaudio.save(
                    temp_file.name, 
                    torch.from_numpy(chunk).unsqueeze(0),
                    self.whisper.sample_rate
                )
                
                # Transcribe
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self.whisper.pipe, temp_file.name
                )
                
                os.unlink(temp_file.name)
                
                transcription = result["text"].strip()
                
                # Determine if this is a final transcription
                is_final = self._is_transcription_final(transcription)
                
                if is_final:
                    self.last_transcription = transcription
                    self.partial_transcripts.clear()
                else:
                    self.partial_transcripts.append(transcription)
                
                return transcription, is_final
                
        except Exception as e:
            print(f"Streaming STT Error: {e}")
            return "", False
    
    def _is_transcription_final(self, transcription: str) -> bool:
        """Determine if transcription is final based on content"""
        # Simple heuristic: if transcription ends with punctuation or is similar to previous
        if not transcription:
            return False
            
        # Check for sentence endings
        if transcription.strip().endswith(('.', '!', '?')):
            return True
            
        # Check for stability (similar to recent transcriptions)
        if len(self.partial_transcripts) >= 2:
            recent = list(self.partial_transcripts)[-2:]
            if all(transcription in prev or prev in transcription for prev in recent):
                return True
                
        return False
    
    async def finalize_transcription(self) -> str:
        """Get final transcription from full buffer"""
        try:
            full_audio = self.audio_buffer.get_full_buffer()
            if len(full_audio) == 0:
                return self.last_transcription
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                torchaudio.save(
                    temp_file.name,
                    torch.from_numpy(full_audio).unsqueeze(0),
                    self.whisper.sample_rate
                )
                
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self.whisper.pipe, temp_file.name
                )
                
                os.unlink(temp_file.name)
                return result["text"].strip()
                
        except Exception as e:
            print(f"Finalize transcription error: {e}")
            return self.last_transcription

# Global instances
whisper_stt = WhisperSTT()

async def transcribe_audio(audio_data: bytes) -> str:
    """Transcribe audio using local Whisper v3 Turbo"""
    
    try:
        # Create temporary file from bytes
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe using pipeline
            result = whisper_stt.pipe(temp_file_path)
            return result["text"].strip()
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        print(f"STT Error: {e}")
        return "Sorry, I couldn't understand what you said."

async def create_streaming_stt() -> StreamingSTT:
    """Create a new streaming STT instance"""
    return StreamingSTT(whisper_stt)
