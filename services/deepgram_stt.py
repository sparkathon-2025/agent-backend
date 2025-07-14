import asyncio
import logging
import os
from typing import Optional, Tuple
from dotenv import load_dotenv
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    PrerecordedOptions,
    FileSource,
)

# Load environment variables
load_dotenv()

# Validate Deepgram API key
def _validate_deepgram_key():
    """Validate that Deepgram API key is present and properly formatted"""
    api_key = os.getenv("DEEPGRAM_API_KEY")
    
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY not found in environment variables")
    
    if len(api_key) < 30:  # Deepgram keys are typically longer
        raise ValueError(f"DEEPGRAM_API_KEY appears to be too short: {len(api_key)} characters")
    
    logging.info(f"Using Deepgram API key: {api_key[:8]}...{api_key[-4:]}")
    return api_key

# Initialize Deepgram client with validation
try:
    api_key = _validate_deepgram_key()
    deepgram_client = DeepgramClient(api_key=api_key)
    logging.info("Deepgram client initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize Deepgram client: {e}")
    raise

async def transcribe_audio(audio_data: bytes) -> str:
    """Transcribe prerecorded audio via Deepgram REST API."""
    try:
        # Log request details
        logging.info(f"Attempting transcription with audio size: {len(audio_data)} bytes")
        
        # Create file source from audio bytes
        payload: FileSource = {
            "buffer": audio_data,
        }
        
        # Configure transcription options
        options = PrerecordedOptions(
            model="nova-2",  # Changed to nova-2 for better compatibility
            language="en-US",
            smart_format=True,
            punctuate=True,
            diarize=False
        )
        
        # Run transcription
        response = await deepgram_client.listen.asyncrest.v("1").transcribe_file(payload, options)
        
        # Extract transcript from response
        if response.results and response.results.channels:
            channel = response.results.channels[0]
            if channel.alternatives:
                transcript = channel.alternatives[0].transcript
                logging.info(f"Transcription successful: {transcript[:50]}...")
                return transcript.strip() if transcript else ""
        
        logging.warning("No transcription results found")
        return ""
        
    except Exception as e:
        logging.error(f"Deepgram STT Error: {e}")
        logging.error(f"Error type: {type(e).__name__}")
        if hasattr(e, 'status_code'):
            logging.error(f"Status code: {e.status_code}")
        return "Sorry, I couldn't understand the audio."

class StreamingDeepgramSTT:
    """Streaming Speech-to-Text processor using Deepgram"""
    
    def __init__(self):
        # Validate key before creating client
        api_key = _validate_deepgram_key()
        self.client = DeepgramClient(api_key=api_key)
        self.connection = None
        self.is_connected = False
        self.transcription_buffer = []
        self.is_finals = []
        self.latest_transcript = ""
        self.latest_is_final = False
        self._connection_ready = False
        
    async def start_streaming(self):
        """Start streaming connection with retry logic"""
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                logging.info(f"Starting Deepgram streaming connection... (attempt {attempt + 1}/{max_retries})")
                
                # Create websocket connection
                self.connection = self.client.listen.asyncwebsocket.v("1")
                
                # Connection ready event
                connection_ready_event = asyncio.Event()
                
                # Set up event handlers
                async def on_open(self, open, **kwargs):
                    logging.info("Deepgram connection opened successfully")
                    self.is_connected = True
                    self._connection_ready = True
                    connection_ready_event.set()
                
                async def on_message(self, result, **kwargs):
                    try:
                        if not result or not result.channel or not result.channel.alternatives:
                            return
                            
                        sentence = result.channel.alternatives[0].transcript
                        if len(sentence) == 0:
                            return
                        
                        self.latest_transcript = sentence
                        self.latest_is_final = result.is_final
                        
                        logging.debug(f"Received transcript: '{sentence}' (final: {result.is_final})")
                        
                        if result.is_final:
                            self.is_finals.append(sentence)
                            self.transcription_buffer.append({
                                "text": sentence,
                                "is_final": True,
                                "speech_final": getattr(result, 'speech_final', False)
                            })
                        else:
                            self.transcription_buffer.append({
                                "text": sentence,
                                "is_final": False,
                                "speech_final": False
                            })
                    except Exception as e:
                        logging.error(f"Error processing transcript: {e}")
                
                async def on_utterance_end(self, utterance_end, **kwargs):
                    try:
                        if len(self.is_finals) > 0:
                            utterance = " ".join(self.is_finals)
                            self.transcription_buffer.append({
                                "text": utterance,
                                "is_final": True,
                                "speech_final": True
                            })
                            self.is_finals = []
                            logging.debug(f"Utterance ended: '{utterance}'")
                    except Exception as e:
                        logging.error(f"Error handling utterance end: {e}")
                
                async def on_error(self, error, **kwargs):
                    logging.error(f"Deepgram streaming error: {error}")
                    self.is_connected = False
                    self._connection_ready = False
                
                async def on_close(self, close, **kwargs):
                    logging.info("Deepgram connection closed")
                    self.is_connected = False
                    self._connection_ready = False
                
                # Register event handlers
                self.connection.on(LiveTranscriptionEvents.Open, on_open)
                self.connection.on(LiveTranscriptionEvents.Transcript, on_message)
                self.connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
                self.connection.on(LiveTranscriptionEvents.Error, on_error)
                self.connection.on(LiveTranscriptionEvents.Close, on_close)
                
                # Configure live transcription options (simplified)
                options = LiveOptions(
                    model="nova-2",
                    language="en-US",
                    smart_format=True,
                    encoding="linear16",
                    channels=1,
                    sample_rate=16000,
                    interim_results=True,
                    utterance_end_ms="1000",
                    vad_events=True,
                )
                
                # Start connection
                connection_result = await self.connection.start(options)
                
                if connection_result is False:
                    raise Exception("Failed to start Deepgram connection")
                
                # Wait for connection to be ready with timeout
                try:
                    await asyncio.wait_for(connection_ready_event.wait(), timeout=10.0)
                    logging.info("Deepgram streaming connection established successfully")
                    return  # Success, exit retry loop
                    
                except asyncio.TimeoutError:
                    raise Exception("Connection ready event not received within timeout")
                
            except Exception as e:
                logging.error(f"Attempt {attempt + 1} failed: {e}")
                
                # Cleanup failed connection
                if self.connection:
                    try:
                        await self.connection.finish()
                    except:
                        pass
                    self.connection = None
                
                self.is_connected = False
                self._connection_ready = False
                
                # If this was the last attempt, raise the error
                if attempt == max_retries - 1:
                    logging.error(f"All {max_retries} connection attempts failed")
                    raise Exception(f"Failed to establish Deepgram connection after {max_retries} attempts: {e}")
                
                # Wait before retrying
                logging.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 1.5  # Exponential backoff
    
    async def send_audio(self, audio_chunk: bytes):
        """Send audio chunk to streaming connection"""
        if self.is_connected and self.connection and self._connection_ready:
            try:
                self.connection.send(audio_chunk)
            except Exception as e:
                logging.error(f"Error sending audio: {e}")
                self.is_connected = False
                self._connection_ready = False
        else:
            logging.warning("Cannot send audio: connection not ready")
    
    def get_latest_transcription(self) -> Tuple[str, bool]:
        """Get latest transcription result"""
        return self.latest_transcript, self.latest_is_final
    
    def get_all_transcriptions(self) -> list:
        """Get all transcription results and clear buffer"""
        results = self.transcription_buffer.copy()
        self.transcription_buffer.clear()
        return results
    
    async def finish_and_get_final(self) -> str:
        """Finish streaming and get final transcription"""
        try:
            if self.connection and self.is_connected:
                # Send finish signal
                await self.connection.finish()
                
                # Wait for any remaining transcriptions
                await asyncio.sleep(0.5)
        except Exception as e:
            logging.error(f"Error finishing connection: {e}")
        
        # Collect all final transcriptions
        final_parts = []
        for result in self.transcription_buffer:
            if result["is_final"]:
                final_parts.append(result["text"])
        
        return " ".join(final_parts).strip()
    
    async def close_connection(self):
        """Close streaming connection"""
        if self.connection:
            try:
                logging.info("Closing Deepgram connection...")
                self.is_connected = False
                
                # Try to finish gracefully first
                try:
                    await asyncio.wait_for(self.connection.finish(), timeout=2.0)
                except asyncio.TimeoutError:
                    logging.warning("Connection finish timed out")
                except Exception as e:
                    logging.warning(f"Error during connection finish: {e}")
                
            except Exception as e:
                logging.error(f"Error closing connection: {e}")
            finally:
                self.connection = None
                logging.info("Deepgram connection closed")

async def create_streaming_deepgram() -> StreamingDeepgramSTT:
    """Create a new streaming Deepgram STT instance"""
    streaming_stt = StreamingDeepgramSTT()
    await streaming_stt.start_streaming()
    return streaming_stt

# Legacy function for compatibility
async def transcribe_live_stream(audio_data: bytes) -> str:
    """Transcribe audio using websocket (for compatibility)"""
    try:
        streaming_stt = await create_streaming_deepgram()
        
        # Send all audio data
        await streaming_stt.send_audio(audio_data)
        
        # Wait a moment for processing
        await asyncio.sleep(1)
        
        # Get final transcription
        result = await streaming_stt.finish_and_get_final()
        await streaming_stt.close_connection()
        
        return result or "Sorry, I couldn't transcribe the audio."
        
    except Exception as e:
        logging.error(f"Live transcription error: {e}")
        return "Sorry, I couldn't transcribe the live audio."