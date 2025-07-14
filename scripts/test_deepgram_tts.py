"""
Script to test Deepgram TTS service with multiple modes:
1. Basic TTS - Generate speech from text
2. Streaming TTS - Real-time text-to-speech streaming
3. Voice comparison - Test different available voices
4. Health check - Test service connectivity

Usage:
    python scripts/test_deepgram_tts.py
"""
import os
import sys
# Ensure project root is in path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import io
import wave
import tempfile
import uuid
from dotenv import load_dotenv
from services.deepgram_tts import (
    generate_speech, 
    generate_speech_streaming,
    add_text_to_stream,
    complete_stream,
    list_available_voices,
    get_tts_health
)

# Load environment variables for Deepgram API key
load_dotenv()

# Try to import audio playback libraries
try:
    import pyaudio
    AUDIO_PLAYBACK_AVAILABLE = True
except ImportError:
    AUDIO_PLAYBACK_AVAILABLE = False
    print("⚠️  PyAudio not available - audio playback disabled")

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


def play_audio_bytes(audio_data: bytes, format_type: str = "mp3"):
    """Play audio bytes using available audio library."""
    
    if not audio_data:
        print("❌ No audio data to play")
        return
    
    try:
        if PYGAME_AVAILABLE and format_type == "mp3":
            # Use pygame for MP3 playback
            pygame.mixer.init()
            
            # Write to temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_file_path = tmp_file.name
            
            try:
                pygame.mixer.music.load(tmp_file_path)
                pygame.mixer.music.play()
                
                print("🔊 Playing audio... (Press Enter to continue)")
                input()  # Wait for user input
                
                pygame.mixer.music.stop()
                pygame.mixer.quit()
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
                    
        elif AUDIO_PLAYBACK_AVAILABLE:
            # Fallback to PyAudio for WAV
            print("🔊 Playing audio via PyAudio...")
            
            # Convert to WAV if needed or assume it's already WAV
            if format_type == "mp3":
                print("⚠️  MP3 playback requires pygame. Converting to WAV not implemented.")
                return
            
            # For WAV data, use PyAudio
            audio = pyaudio.PyAudio()
            
            # Parse WAV header to get parameters
            with io.BytesIO(audio_data) as wav_io:
                with wave.open(wav_io, 'rb') as wav_file:
                    sample_rate = wav_file.getframerate()
                    channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
                    audio_frames = wav_file.readframes(wav_file.getnframes())
            
            # Configure PyAudio stream
            stream = audio.open(
                format=audio.get_format_from_width(sample_width),
                channels=channels,
                rate=sample_rate,
                output=True
            )
            
            print("🔊 Playing audio... (Press Enter to continue)")
            
            # Play audio
            stream.write(audio_frames)
            input()  # Wait for user input
            
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
        else:
            print("❌ No audio playback library available")
            print("💡 Install pygame: pip install pygame")
            print("💡 Or install pyaudio: pip install pyaudio")
            
            # Save to file as fallback
            filename = f"test_tts_output_{uuid.uuid4().hex[:8]}.mp3"
            with open(filename, 'wb') as f:
                f.write(audio_data)
            print(f"💾 Audio saved to: {filename}")
            
    except Exception as e:
        print(f"❌ Error playing audio: {e}")
        
        # Save to file as fallback
        try:
            filename = f"test_tts_output_{uuid.uuid4().hex[:8]}.{format_type}"
            with open(filename, 'wb') as f:
                f.write(audio_data)
            print(f"💾 Audio saved to: {filename}")
        except Exception as save_error:
            print(f"❌ Failed to save audio: {save_error}")


async def test_basic_tts():
    """Test basic text-to-speech functionality."""
    print("\n=== Basic TTS Test ===")
    
    test_texts = [
        "Hello, this is a test of Deepgram text to speech.",
        "The quick brown fox jumps over the lazy dog.",
        "Testing different sentence lengths and punctuation! How does this sound?",
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n🎯 Test {i}: {text[:50]}...")
        
        try:
            # Generate speech
            print("🔄 Generating speech...")
            audio_data = await generate_speech(
                text=text,
                voice="alloy",  # Default voice
                response_format="mp3"
            )
            
            if audio_data:
                print(f"✅ Generated {len(audio_data)} bytes of audio")
                
                # Play audio if possible
                play_audio_bytes(audio_data, "mp3")
                
            else:
                print("❌ No audio data generated")
                
        except Exception as e:
            print(f"❌ Error in test {i}: {e}")


async def test_voice_comparison():
    """Test different available voices."""
    print("\n=== Voice Comparison Test ===")
    
    # Get available voices
    try:
        voices = await list_available_voices()
        print(f"📋 Found {len(voices)} available voices")
        
        # Test text
        test_text = "Hello, I am testing the Deepgram text to speech voice."
        
        # Test a few different voices
        test_voices = ["alloy", "echo", "nova", "aura-2-thalia-en"]
        
        for voice in test_voices:
            # Check if voice is available
            voice_info = next((v for v in voices if v["voice_id"] == voice), None)
            if not voice_info:
                print(f"⚠️  Voice {voice} not found in available voices")
                continue
                
            print(f"\n🎭 Testing voice: {voice_info['name']} ({voice})")
            print(f"   Description: {voice_info['description']}")
            
            try:
                audio_data = await generate_speech(
                    text=test_text,
                    voice=voice,
                    response_format="mp3"
                )
                
                if audio_data:
                    print(f"✅ Generated {len(audio_data)} bytes")
                    
                    # Ask user if they want to hear it
                    choice = input(f"🔊 Play {voice_info['name']} voice? (y/n/s=skip all): ").strip().lower()
                    if choice == 's':
                        print("⏭️  Skipping remaining voice tests")
                        break
                    elif choice in ['y', 'yes', '']:
                        play_audio_bytes(audio_data, "mp3")
                else:
                    print("❌ No audio generated")
                    
            except Exception as e:
                print(f"❌ Error testing voice {voice}: {e}")
                
    except Exception as e:
        print(f"❌ Error in voice comparison: {e}")


async def test_streaming_tts():
    """Test streaming text-to-speech functionality."""
    print("\n=== Streaming TTS Test ===")
    print("This will simulate real-time text streaming to speech")
    
    # Text chunks to stream
    text_chunks = [
        "Welcome to the streaming text to speech test.",
        "This sentence is being sent in real time.",
        "Each chunk of text is processed as it arrives.",
        "This simulates how a chatbot would speak.",
        "Thank you for testing the streaming functionality."
    ]
    
    session_id = str(uuid.uuid4())
    print(f"🆔 Session ID: {session_id}")
    
    try:
        # Collect all audio chunks
        audio_chunks = []
        chunk_count = 0
        
        print("🔄 Starting streaming TTS...")
        
        # Start the streaming task
        streaming_task = asyncio.create_task(
            _collect_streaming_audio(session_id, audio_chunks)
        )
        
        # Send text chunks with delays
        for i, chunk in enumerate(text_chunks, 1):
            print(f"📤 Sending chunk {i}: {chunk}")
            add_text_to_stream(session_id, chunk)
            
            # Wait a bit between chunks to simulate real-time
            await asyncio.sleep(1.0)
        
        # Complete the stream
        print("🏁 Completing stream...")
        complete_stream(session_id)
        
        # Wait for streaming to finish
        await asyncio.sleep(2.0)
        streaming_task.cancel()
        
        # Combine all audio chunks
        if audio_chunks:
            total_audio = b''.join(audio_chunks)
            print(f"✅ Collected {len(audio_chunks)} audio chunks, {len(total_audio)} total bytes")
            
            # Play combined audio
            choice = input("🔊 Play streaming result? (y/n): ").strip().lower()
            if choice in ['y', 'yes', '']:
                play_audio_bytes(total_audio, "mp3")
        else:
            print("❌ No audio chunks received")
            
    except Exception as e:
        print(f"❌ Streaming TTS error: {e}")


async def _collect_streaming_audio(session_id: str, audio_chunks: list):
    """Helper to collect streaming audio chunks."""
    try:
        async for audio_chunk in generate_speech_streaming(session_id):
            if audio_chunk:
                audio_chunks.append(audio_chunk)
                print(f"🎵 Received audio chunk: {len(audio_chunk)} bytes")
    except asyncio.CancelledError:
        print("🛑 Streaming collection cancelled")
    except Exception as e:
        print(f"❌ Error collecting streaming audio: {e}")


async def test_health_check():
    """Test TTS service health and connectivity."""
    print("\n=== Health Check ===")
    
    try:
        health_status = await get_tts_health()
        
        print("🏥 Service Health Status:")
        print(f"   Status: {health_status.get('status', 'unknown')}")
        print(f"   Service: {health_status.get('service', 'unknown')}")
        print(f"   API Key Configured: {health_status.get('api_key_configured', False)}")
        print(f"   Voices Available: {health_status.get('voices_available', 0)}")
        
        if health_status.get('error'):
            print(f"   Error: {health_status['error']}")
        
        # Test basic functionality
        if health_status.get('status') == 'healthy':
            print("✅ Service is healthy")
        else:
            print("❌ Service has issues")
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")


async def test_error_handling():
    """Test error handling with invalid inputs."""
    print("\n=== Error Handling Test ===")
    
    test_cases = [
        ("", "Empty text"),
        ("x" * 5000, "Very long text"),
        ("Hello", "invalid_voice", "Invalid voice"),
        ("Hello", "alloy", "invalid_format", "Invalid format"),
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        text = test_case[0]
        voice = test_case[1] if len(test_case) > 2 else "alloy"
        format_type = test_case[2] if len(test_case) > 3 else "mp3"
        description = test_case[-1]
        
        print(f"\n🧪 Error Test {i}: {description}")
        
        try:
            if len(test_case) == 4:  # Invalid format test
                audio_data = await generate_speech(
                    text=text,
                    voice=voice,
                    response_format=format_type
                )
            else:
                audio_data = await generate_speech(
                    text=text,
                    voice=voice
                )
            
            if audio_data:
                print(f"⚠️  Unexpected success: {len(audio_data)} bytes generated")
            else:
                print("✅ Handled gracefully: No audio generated")
                
        except Exception as e:
            print(f"✅ Error handled: {e}")


async def main():
    """Main function with menu selection."""
    
    # Check for Deepgram API key
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
    
    # Audio setup info
    if AUDIO_PLAYBACK_AVAILABLE or PYGAME_AVAILABLE:
        libraries = []
        if PYGAME_AVAILABLE:
            libraries.append("pygame")
        if AUDIO_PLAYBACK_AVAILABLE:
            libraries.append("pyaudio")
        print(f"🔊 Audio playback available: {', '.join(libraries)}")
    else:
        print("⚠️  No audio playback libraries available")
        print("💡 Install: pip install pygame pyaudio")
    
    print("\n🎤 Deepgram TTS Test Script")
    print("=" * 50)
    print("Choose a test mode:")
    print("1. 🎯 Basic TTS Test")
    print("2. 🎭 Voice Comparison Test") 
    print("3. 📡 Streaming TTS Test")
    print("4. 🏥 Health Check")
    print("5. 🧪 Error Handling Test")
    print("6. 🔄 Run All Tests")
    
    while True:
        try:
            choice = input("\nSelect test (1-6) or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                print("👋 Goodbye!")
                break
            
            if choice == '1':
                await test_basic_tts()
            elif choice == '2':
                await test_voice_comparison()
            elif choice == '3':
                await test_streaming_tts()
            elif choice == '4':
                await test_health_check()
            elif choice == '5':
                await test_error_handling()
            elif choice == '6':
                print("\n🔄 Running all tests...")
                await test_health_check()
                await test_basic_tts()
                await test_voice_comparison()
                await test_streaming_tts()
                await test_error_handling()
                print("\n✅ All tests completed!")
            else:
                print("❌ Invalid choice. Please select 1-6 or 'q' to quit.")
                continue
                
            # Ask if user wants to continue
            continue_choice = input("\nWould you like to run another test? (y/n): ").strip().lower()
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
