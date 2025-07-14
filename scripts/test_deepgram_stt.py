"""
Script to test Deepgram STT service with two modes:
1. Live transcription - real-time speech to text
2. Recorded transcription - record first, then transcribe

Usage:
    python scripts/test_deepgram_stt.py
"""
import os
import sys
# Ensure project root is in path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import io
import wave
import pyaudio
from dotenv import load_dotenv
from services.deepgram_stt import transcribe_audio, create_streaming_deepgram

# Load environment variables for Deepgram API key
load_dotenv()

# Audio recording parameters
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK = 1024
FORMAT = pyaudio.paInt16
RECORD_SECONDS = 5  # seconds to record for option 2


def record_audio_to_wav(duration=RECORD_SECONDS) -> bytes:
    """Record audio from default microphone and return WAV data as bytes."""
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
    
    print(f"Recording for {duration} seconds...")
    frames = []
    for _ in range(0, int(SAMPLE_RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Recording complete.")
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Write WAV header into BytesIO
    buffer = io.BytesIO()
    wf = wave.open(buffer, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    return buffer.getvalue()


async def test_live_transcription():
    """Test live transcription - real-time speech to text"""
    print("\n=== Live Transcription Mode ===")
    print("This will transcribe your speech in real-time.")
    print("Speak clearly into your microphone. Press Ctrl+C to stop.\n")
    
    streaming_stt = None
    audio = None
    stream = None
    
    try:
        # Test basic API connectivity first
        print("🔍 Testing Deepgram API connectivity...")
        try:
            # Quick test with recorded transcription
            test_audio = b'\x00' * 1024  # Simple test audio
            await transcribe_audio(test_audio)
            print("✅ Deepgram API is accessible")
        except Exception as e:
            print(f"❌ Deepgram API test failed: {e}")
            print("Please check your API key and internet connection")
            return
        
        # Create streaming STT instance
        print("🔗 Connecting to Deepgram streaming...")
        streaming_stt = await create_streaming_deepgram()
        
        if not streaming_stt.is_connected:
            print("❌ Failed to connect to Deepgram streaming API")
            print("💡 Tip: Streaming requires a paid Deepgram plan")
            print("💡 Tip: Try using recorded transcription mode instead")
            return
        
        print("✅ Connected to Deepgram successfully!")
        
        # Test audio setup
        print("🎤 Testing audio setup...")
        try:
            audio = pyaudio.PyAudio()
            
            # Test if we can open the audio stream
            test_stream = audio.open(format=FORMAT,
                                   channels=CHANNELS,
                                   rate=SAMPLE_RATE,
                                   input=True,
                                   frames_per_buffer=CHUNK)
            test_stream.close()
            print("✅ Audio system ready")
            
        except Exception as e:
            print(f"❌ Audio setup failed: {e}")
            print("💡 Tip: Check microphone permissions and connections")
            return
        
        # Start audio stream
        stream = audio.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=SAMPLE_RATE,
                            input=True,
                            frames_per_buffer=CHUNK)
        
        print("🎤 Listening... Speak now!")
        print("Press Ctrl+C to stop\n")
        
        # Track last transcription to avoid duplicates
        last_transcript = ""
        chunks_sent = 0
        
        while True:
            try:
                # Read audio chunk
                data = stream.read(CHUNK, exception_on_overflow=False)
                chunks_sent += 1
                
                # Send to Deepgram
                await streaming_stt.send_audio(data)
                
                # Check for transcription results
                text, is_final = streaming_stt.get_latest_transcription()
                
                # Only print if we have new text
                if text and text != last_transcript:
                    status = "FINAL" if is_final else "interim"
                    print(f"[{status.upper()}] {text}")
                    last_transcript = text
                
                # Show activity indicator every 100 chunks
                if chunks_sent % 100 == 0:
                    print(f"📡 Sent {chunks_sent} audio chunks...")
                    
                # Small delay to prevent overwhelming the API
                await asyncio.sleep(0.01)
                
            except KeyboardInterrupt:
                print("\n⚠️  Stopping by user request...")
                break
            except Exception as e:
                print(f"❌ Error during transcription: {e}")
                break
    
    except Exception as e:
        print(f"❌ Error in live transcription: {e}")
        
        # Suggest alternatives
        print("\n💡 Troubleshooting suggestions:")
        print("1. Check your Deepgram API key is valid and active")
        print("2. Ensure you have a paid Deepgram plan (streaming requires credits)")
        print("3. Check your internet connection")
        print("4. Try recorded transcription mode instead")
        print("5. Check Deepgram service status: https://status.deepgram.com/")
    
    finally:
        print("\n🛑 Stopping live transcription...")
        
        # Close audio stream first
        if stream:
            try:
                stream.stop_stream()
                stream.close()
                print("✅ Audio stream closed")
            except Exception as e:
                print(f"⚠️  Error closing audio stream: {e}")
        
        if audio:
            try:
                audio.terminate()
                print("✅ Audio system terminated")
            except Exception as e:
                print(f"⚠️  Error terminating audio: {e}")
        
        # Close Deepgram connection
        if streaming_stt:
            try:
                await streaming_stt.close_connection()
                print("✅ Deepgram connection closed")
            except Exception as e:
                print(f"⚠️  Error closing Deepgram connection: {e}")
        
        print("✅ Cleanup complete")


async def test_recorded_transcription():
    """Test recorded transcription - record audio then transcribe"""
    print("\n=== Recorded Transcription Mode ===")
    print("This will record your voice for 5 seconds, then transcribe it.")
    
    try:
        # Record audio
        wav_bytes = record_audio_to_wav()
        
        # Transcribe using prerecorded API
        print("Transcribing recorded audio...")
        transcription = await transcribe_audio(wav_bytes)
        
        print(f"\n📝 Final Transcription: {transcription}")
        
    except Exception as e:
        print(f"Error in recorded transcription: {e}")


async def main():
    """Main function with menu selection"""
    
    # Check for Deepgram API key with detailed validation
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        print("❌ Error: DEEPGRAM_API_KEY not found in environment variables")
        print("Please add your Deepgram API key to the .env file")
        return
    
    # Validate API key format
    if len(api_key) < 30:
        print(f"❌ Error: DEEPGRAM_API_KEY appears to be invalid (too short: {len(api_key)} characters)")
        print("Please check your API key in the .env file")
        return
    
    print(f"✅ Using Deepgram API key: {api_key[:8]}...{api_key[-4:]}")
    
    print("🎙️  Deepgram STT Test Script")
    print("=" * 50)
    print("Choose a transcription mode:")
    print("1. 🔴 Live Transcription (real-time) - Requires paid plan")
    print("2. 📼 Recorded Transcription (record then transcribe)")
    
    while True:
        try:
            choice = input("\nSelect mode (1-2) or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                print("👋 Goodbye!")
                break
            
            if choice == '1':
                await test_live_transcription()
            elif choice == '2':
                await test_recorded_transcription()
            else:
                print("❌ Invalid choice. Please select 1, 2, or 'q' to quit.")
                continue
                
            # Ask if user wants to continue
            continue_choice = input("\nWould you like to test another mode? (y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes']:
                print("👋 Goodbye!")
                break
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user.")
