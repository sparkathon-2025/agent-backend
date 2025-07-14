import asyncio
import aiohttp
import websockets
import json
import base64
import os
import sys
import wave
import numpy as np
from pathlib import Path
import threading
import time

# Add audio libraries
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("⚠️  PyAudio not available. Install with: pip install pyaudio")

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("⚠️  Pygame not available. Install with: pip install pygame")

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/voice-agent/stream"

# Sample product data from populate script
SAMPLE_PRODUCTS = {
    "prod_001": {"store_id": "store_001", "name": "Amul Butter", "price": 45.0, "stock": 25},
    "prod_002": {"store_id": "store_001", "name": "Amul Milk", "price": 28.0, "stock": 40},
    "prod_003": {"store_id": "store_001", "name": "Britannia Good Day Cookies", "price": 20.0, "stock": 60},
    "prod_004": {"store_id": "store_001", "name": "Maggi 2-Minute Noodles", "price": 14.0, "stock": 80},
}

SAMPLE_STORES = {
    "store_001": {"name": "Fresh Mart Downtown", "address": "123 Main Street"},
    "store_002": {"name": "Quick Shop Plaza", "address": "456 Oak Avenue"},
}

# ...existing code...

class VoiceAgentTester:
    def __init__(self):
        self.session = None
        self.recording = False
        self.available_voices = []
        self.selected_voice = None
        
        # Audio settings
        self.chunk = 1024
        self.format = pyaudio.paInt16 if PYAUDIO_AVAILABLE else None
        self.channels = 1
        self.rate = 16000
        
        # Initialize pygame mixer for audio playback
        if PYGAME_AVAILABLE:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

    # ...existing code...

    async def get_available_voices(self):
        """Fetch available voices from the server"""
        try:
            async with websockets.connect(WS_URL) as websocket:
                await websocket.send(json.dumps({"type": "start_session"}))
                await websocket.recv()  # Wait for session start
                
                await websocket.send(json.dumps({"type": "get_voices"}))
                response = await websocket.recv()
                data = json.loads(response)
                
                if data.get("type") == "voices":
                    self.available_voices = data["voices"]
                    return True
                else:
                    print(f"❌ Failed to get voices: {data}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error fetching voices: {e}")
            return False

    def display_voice_menu(self):
        """Display voice selection menu"""
        print("\n" + "="*50)
        print("🎤 VOICE SELECTION")
        print("="*50)
        
        if not self.available_voices:
            print("❌ No voices available")
            return None
            
        for i, voice in enumerate(self.available_voices, 1):
            print(f"{i}. {voice['name']} ({voice['type']}) - {voice['voice_id']}")
        
        while True:
            try:
                choice = input(f"\nSelect voice (1-{len(self.available_voices)}): ").strip()
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(self.available_voices):
                    self.selected_voice = self.available_voices[choice_idx]
                    print(f"✅ Selected: {self.selected_voice['name']}")
                    return self.selected_voice
                else:
                    print("❌ Invalid choice")
            except ValueError:
                print("❌ Please enter a number")

    def display_endpoint_menu(self):
        """Display endpoint selection menu"""
        print("\n" + "="*50)
        print("🔗 ENDPOINT SELECTION")
        print("="*50)
        print("1. REST API (Single request/response)")
        print("2. WebSocket (Streaming)")
        
        while True:
            choice = input("\nSelect endpoint (1-2): ").strip()
            if choice == "1":
                return "rest"
            elif choice == "2":
                return "websocket"
            else:
                print("❌ Invalid choice")

    def display_store_menu(self):
        """Display store selection menu"""
        print("\n" + "="*50)
        print("🏪 STORE SELECTION")
        print("="*50)
        
        stores = list(SAMPLE_STORES.items())
        for i, (store_id, store_info) in enumerate(stores, 1):
            print(f"{i}. {store_info['name']} - {store_info['address']}")
        
        while True:
            try:
                choice = input(f"\nSelect store (1-{len(stores)}): ").strip()
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(stores):
                    store_id, store_info = stores[choice_idx]
                    print(f"✅ Selected: {store_info['name']}")
                    return store_id
                else:
                    print("❌ Invalid choice")
            except ValueError:
                print("❌ Please enter a number")

    def display_product_menu(self):
        """Display product selection menu"""
        print("\n" + "="*50)
        print("🛍️  PRODUCT SELECTION")
        print("="*50)
        
        products = list(SAMPLE_PRODUCTS.items())
        for i, (prod_id, prod_info) in enumerate(products, 1):
            print(f"{i}. {prod_info['name']} - ₹{prod_info['price']} (Stock: {prod_info['stock']})")
        
        while True:
            try:
                choice = input(f"\nSelect product (1-{len(products)}): ").strip()
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(products):
                    prod_id, prod_info = products[choice_idx]
                    print(f"✅ Selected: {prod_info['name']}")
                    return prod_id, prod_info
                else:
                    print("❌ Invalid choice")
            except ValueError:
                print("❌ Please enter a number")

    # ...existing code...

    async def interactive_voice_chat_rest(self, store_id, product_id):
        """Interactive voice chat using REST endpoint"""
        print("\n" + "="*50)
        print("🎤 VOICE CHAT - REST MODE")
        print("="*50)
        print("Press 'r' to record and ask a question")
        print("Press 'q' to quit")
        print("Your responses will be played back automatically")
        
        while True:
            print("\n" + "-"*30)
            choice = input("Action (r/q): ").lower().strip()
            
            if choice == 'q':
                break
            elif choice == 'r':
                # Record audio
                audio_data = self.record_audio()
                if not audio_data:
                    print("❌ Recording failed")
                    continue
                
                print("🔄 Processing your question...")
                
                # Prepare form data
                data = aiohttp.FormData()
                data.add_field('audio', audio_data, 
                             filename='user_question.wav', 
                             content_type='audio/wav')
                data.add_field('product_id', product_id)
                data.add_field('store_id', store_id)
                if self.selected_voice:
                    data.add_field('voice_id', self.selected_voice['voice_id'])
                
                try:
                    async with self.session.post(
                        f"{BASE_URL}/voice-agent/query",
                        data=data
                    ) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            print(f"\n🤖 Agent: {result['text']}")
                            
                            # Play audio response immediately
                            if result.get('audio'):
                                print("🔊 Playing response...")
                                self.play_audio(result['audio'])
                            else:
                                print("⚠️  No audio in response")
                                
                        else:
                            error_text = await response.text()
                            print(f"❌ Error {response.status}: {error_text}")
                            
                except Exception as e:
                    print(f"❌ Request failed: {e}")
            else:
                print("❌ Invalid choice. Use 'r' to record or 'q' to quit")

    async def interactive_voice_chat_websocket(self, store_id, product_info):
        """Interactive voice chat using WebSocket streaming"""
        print("\n" + "="*50)
        print("🎤 VOICE CHAT - WEBSOCKET STREAMING")
        print("="*50)
        print("Press 's' to speak and ask a question")
        print("Press 'q' to quit")
        print("Responses will stream back in real-time")
        
        try:
            async with websockets.connect(WS_URL) as websocket:
                
                # Start session
                await websocket.send(json.dumps({"type": "start_session"}))
                response = await websocket.recv()
                session_data = json.loads(response)
                print(f"✅ Session started: {session_data.get('session_id', 'unknown')}")
                
                # Set voice if selected
                if self.selected_voice:
                    await websocket.send(json.dumps({
                        "type": "set_voice",
                        "voice_id": self.selected_voice['voice_id']
                    }))
                
                while True:
                    print("\n" + "-"*30)
                    choice = input("Action (s/q): ").lower().strip()
                    
                    if choice == 'q':
                        break
                    elif choice == 's':
                        # Record audio
                        print("🎤 Start speaking...")
                        audio_data = self.record_audio()
                        if not audio_data:
                            print("❌ Recording failed")
                            continue
                        
                        print("🔄 Streaming to agent...")
                        
                        # Send audio in chunks
                        chunk_size = 4096
                        audio_chunks = [audio_data[i:i+chunk_size] 
                                       for i in range(0, len(audio_data), chunk_size)]
                        
                        for chunk in audio_chunks:
                            await websocket.send(json.dumps({
                                "type": "audio_chunk",
                                "audio": base64.b64encode(chunk).decode('utf-8'),
                                "product_context": product_info,
                                "store_id": store_id
                            }))
                            await asyncio.sleep(0.05)
                        
                        # End audio
                        await websocket.send(json.dumps({
                            "type": "end_audio",
                            "product_context": product_info,
                            "store_id": store_id
                        }))
                        
                        # Handle responses
                        response_text = ""
                        audio_chunks = []
                        
                        while True:
                            try:
                                response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                                data = json.loads(response)
                                
                                msg_type = data.get("type")
                                
                                if msg_type == "transcript":
                                    if data.get('is_final'):
                                        print(f"🎤 You said: {data['text']}")
                                
                                elif msg_type == "response_chunk":
                                    response_text += data['text']
                                    print(f"🤖 {data['text']}", end=" ", flush=True)
                                
                                elif msg_type == "audio_chunk":
                                    audio_chunks.append(data['audio'])
                                
                                elif msg_type == "response_complete":
                                    print(f"\n✅ Complete response received")
                                    
                                    # Play audio immediately
                                    if audio_chunks:
                                        print("🔊 Playing response...")
                                        combined_audio = b""
                                        for chunk_b64 in audio_chunks:
                                            combined_audio += base64.b64decode(chunk_b64)
                                        self.play_audio(combined_audio, is_base64=False)
                                    
                                    break
                                
                                elif msg_type == "error":
                                    print(f"\n❌ Error: {data['message']}")
                                    break
                                    
                            except asyncio.TimeoutError:
                                print("\n⏰ Response timeout")
                                break
                    else:
                        print("❌ Invalid choice. Use 's' to speak or 'q' to quit")
                        
        except Exception as e:
            print(f"❌ WebSocket error: {e}")

    # ...existing code...

async def run_interactive_voice_test():
    """Run the simplified interactive voice test"""
    print("🚀 Voice Agent Interactive Test")
    print("Make sure the server is running on http://localhost:8000")
    
    if not PYAUDIO_AVAILABLE:
        print("❌ PyAudio is required for voice testing. Install with: pip install pyaudio")
        return
    
    if not PYGAME_AVAILABLE:
        print("❌ Pygame is required for audio playback. Install with: pip install pygame")
        return
    
    # Check server connection
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/") as response:
                if response.status != 200:
                    print("❌ Server not responding correctly")
                    return
                print("✅ Server is running")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    async with VoiceAgentTester() as tester:
        # Step 1: Get available voices
        print("🔄 Fetching available voices...")
        if not await tester.get_available_voices():
            print("❌ Could not fetch voices. Continuing without voice selection...")
        
        # Step 2: Voice selection
        if tester.available_voices:
            voice = tester.display_voice_menu()
        else:
            print("⚠️  No voice selection available")
        
        # Step 3: Endpoint selection
        endpoint = tester.display_endpoint_menu()
        
        # Step 4: Store selection
        store_id = tester.display_store_menu()
        
        # Step 5: Product selection
        product_id, product_info = tester.display_product_menu()
        
        # Step 6: Start voice chat
        print(f"\n🎉 Starting voice chat with {endpoint.upper()} endpoint")
        print(f"Store: {SAMPLE_STORES[store_id]['name']}")
        print(f"Product: {product_info['name']}")
        if tester.selected_voice:
            print(f"Voice: {tester.selected_voice['name']}")
        
        if endpoint == "rest":
            await tester.interactive_voice_chat_rest(store_id, product_id)
        else:
            await tester.interactive_voice_chat_websocket(store_id, product_info)
    
    print("\n🎉 Voice chat session ended!")

def main():
    """Main test runner"""
    try:
        asyncio.run(run_interactive_voice_test())
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")

if __name__ == "__main__":
    main()
            
        finally:
            p.terminate()

    def play_audio(self, audio_data, is_base64=True):
        """Play audio data"""
        if not PYGAME_AVAILABLE:
            print("❌ Pygame not available for playback")
            return
            
        try:
            if is_base64:
                audio_data = base64.b64decode(audio_data)
            
            # Save to temp file and play
            temp_file = "temp_playback.mp3"
            with open(temp_file, 'wb') as f:
                f.write(audio_data)
            
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # Clean up
            os.remove(temp_file)
            
        except Exception as e:
            print(f"❌ Playback error: {e}")

    async def test_interactive_voice_rest(self):
        """Interactive voice test using REST endpoint"""
        print("\n" + "="*50)
        print("INTERACTIVE VOICE TEST - REST ENDPOINT")
        print("="*50)
        
        if not PYAUDIO_AVAILABLE:
            print("❌ PyAudio required for interactive voice testing")
            return
        
        # Product selection
        print("\nAvailable products for testing:")
        for prod_id, prod_info in SAMPLE_PRODUCTS.items():
            print(f"  {prod_id}: {prod_info['name']}")
        
        product_id = input("\nEnter product ID (or press Enter for prod_001): ").strip()
        if not product_id:
            product_id = "prod_001"
        
        store_id = "store_001"
        
        print(f"\n🛍️  Testing with: {SAMPLE_PRODUCTS.get(product_id, {}).get('name', 'Unknown Product')}")
        print("\nInteractive Voice Session Started!")
        print("You can ask questions about the product, store location, prices, etc.")
        
        while True:
            print("\n" + "-"*30)
            choice = input("Press 'r' to record question, 'q' to quit: ").lower()
            
            if choice == 'q':
                break
            elif choice == 'r':
                # Record audio
                audio_data = self.record_audio()
                if not audio_data:
                    print("❌ Recording failed")
                    continue
                
                print("🔄 Processing your question...")
                
                # Prepare form data
                data = aiohttp.FormData()
                data.add_field('audio', audio_data, 
                             filename='user_question.wav', 
                             content_type='audio/wav')
                data.add_field('product_id', product_id)
                data.add_field('store_id', store_id)
                
                try:
                    # Make request
                    async with self.session.post(
                        f"{BASE_URL}/voice-agent/query",
                        data=data
                    ) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            print(f"🤖 Agent Response: {result['text']}")
                            
                            # Play audio response
                            if result.get('audio'):
                                print("🔊 Playing audio response...")
                                self.play_audio(result['audio'])
                            else:
                                print("⚠️  No audio in response")
                                
                        else:
                            error_text = await response.text()
                            print(f"❌ Error {response.status}: {error_text}")
                            
                except Exception as e:
                    print(f"❌ Request failed: {e}")
            else:
                print("❌ Invalid choice")

    async def test_interactive_voice_websocket(self):
        """Interactive voice test using WebSocket streaming"""
        print("\n" + "="*50)
        print("INTERACTIVE VOICE TEST - WEBSOCKET STREAMING")
        print("="*50)
        
        if not PYAUDIO_AVAILABLE:
            print("❌ PyAudio required for interactive voice testing")
            return
        
        # Product context setup
        product_context = {
            "id": "prod_002",
            "name": "Amul Milk",
            "brand": "Amul", 
            "price": 28.0,
            "stock": 40
        }
        store_id = "store_001"
        
        print(f"🛍️  Product Context: {product_context['name']} - ₹{product_context['price']}")
        print("Real-time Voice Streaming Session!")
        
        try:
            async with websockets.connect(WS_URL) as websocket:
                
                # Start session
                await websocket.send(json.dumps({"type": "start_session"}))
                response = await websocket.recv()
                session_data = json.loads(response)
                print(f"✅ Session started: {session_data.get('session_id', 'unknown')}")
                
                while True:
                    print("\n" + "-"*30)
                    choice = input("Press 's' to speak, 'q' to quit: ").lower()
                    
                    if choice == 'q':
                        break
                    elif choice == 's':
                        # Record audio
                        print("🎤 Start speaking your question...")
                        audio_data = self.record_audio()
                        if not audio_data:
                            print("❌ Recording failed")
                            continue
                        
                        print("🔄 Streaming audio to agent...")
                        
                        # Send audio in chunks for streaming
                        chunk_size = 4096
                        audio_chunks = [audio_data[i:i+chunk_size] 
                                       for i in range(0, len(audio_data), chunk_size)]
                        
                        # Send chunks
                        for i, chunk in enumerate(audio_chunks):
                            await websocket.send(json.dumps({
                                "type": "audio_chunk",
                                "audio": base64.b64encode(chunk).decode('utf-8'),
                                "product_context": product_context,
                                "store_id": store_id
                            }))
                            await asyncio.sleep(0.1)  # Small delay between chunks
                        
                        # End audio
                        await websocket.send(json.dumps({
                            "type": "end_audio",
                            "product_context": product_context,
                            "store_id": store_id
                        }))
                        
                        # Collect responses
                        response_text = ""
                        audio_chunks = []
                        
                        print("🔄 Waiting for agent response...")
                        
                        while True:
                            try:
                                response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                                data = json.loads(response)
                                
                                msg_type = data.get("type")
                                
                                if msg_type == "transcript":
                                    if data.get('is_final'):
                                        print(f"🎤 You said: {data['text']}")
                                
                                elif msg_type == "response_chunk":
                                    response_text += data['text']
                                    print(f"🤖 {data['text']}", end="", flush=True)
                                
                                elif msg_type == "audio_chunk":
                                    audio_chunks.append(data['audio'])
                                
                                elif msg_type == "response_complete":
                                    print(f"\n✅ Complete Response: {data['full_text']}")
                                    
                                    # Play combined audio response
                                    if audio_chunks:
                                        print("🔊 Playing audio response...")
                                        combined_audio = b""
                                        for chunk_b64 in audio_chunks:
                                            combined_audio += base64.b64decode(chunk_b64)
                                        self.play_audio(combined_audio, is_base64=False)
                                    
                                    break
                                
                                elif msg_type == "error":
                                    print(f"\n❌ Error: {data['message']}")
                                    break
                                    
                            except asyncio.TimeoutError:
                                print("\n⏰ Response timeout")
                                break
                    else:
                        print("❌ Invalid choice")
                        
        except Exception as e:
            print(f"❌ WebSocket error: {e}")

async def run_all_tests():
    """Run all voice agent tests"""
    print("🚀 Starting Voice Agent Tests")
    print("Make sure the server is running on http://localhost:8000")
    
    # Check if server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/") as response:
                if response.status != 200:
                    print("❌ Server not responding correctly")
                    return
                print("✅ Server is running")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Make sure to run: python main.py")
        return
    
    # Test selection menu
    print("\n" + "="*50)
    print("VOICE AGENT TEST MENU")
    print("="*50)
    print("1. Interactive Voice Test (REST)")
    print("2. Interactive Voice Test (WebSocket)")
    print("3. Automated Tests (Original)")
    print("4. All Tests")
    
    choice = input("\nSelect test type (1-4): ").strip()
    
    async with VoiceAgentTester() as tester:
        if choice == "1":
            await tester.test_interactive_voice_rest()
        elif choice == "2":
            await tester.test_interactive_voice_websocket()
        elif choice == "3":
            # Run original automated tests
            await tester.test_voice_list()
            await tester.test_rest_endpoint()
            await tester.test_websocket_endpoint()
        elif choice == "4":
            # Run all tests
            await tester.test_voice_list()
            await tester.test_rest_endpoint()
            await tester.test_websocket_endpoint()
            await tester.test_interactive_voice_rest()
            await tester.test_interactive_voice_websocket()
        else:
            print("❌ Invalid choice, running automated tests")
            await tester.test_voice_list()
            await tester.test_rest_endpoint()
            await tester.test_websocket_endpoint()
    
    print("\n" + "="*50)
    print("🎉 TESTS COMPLETED")
    print("="*50)

def main():
    """Main test runner"""
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")

if __name__ == "__main__":
    main()
