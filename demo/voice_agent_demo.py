import asyncio
import sys
import os
import json
import pyaudio
import wave
import tempfile
import threading
from typing import Dict, Any
import io

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.mongo import connect_to_mongo, get_database, close_mongo_connection
from services.gpt_agent import process_query, process_query_streaming
from services.sesame_tts import generate_speech
from services.whisper_stt import transcribe_audio, create_streaming_stt
from services.product_query import get_product_context
from dotenv import load_dotenv

load_dotenv()

class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1, chunk_size=1024):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format = pyaudio.paFloat32
        self.frames = []
        self.is_recording = False
        self.audio = pyaudio.PyAudio()
        
    def start_recording(self):
        """Start recording audio"""
        self.frames = []
        self.is_recording = True
        
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        print("🎤 Recording... (Press Enter to stop)")
        
        def record():
            while self.is_recording:
                data = stream.read(self.chunk_size)
                self.frames.append(data)
        
        record_thread = threading.Thread(target=record)
        record_thread.start()
        
        # Wait for user input to stop recording
        input()
        self.is_recording = False
        record_thread.join()
        
        stream.stop_stream()
        stream.close()
        
        return self.get_audio_bytes()
    
    def get_audio_bytes(self):
        """Convert recorded frames to bytes"""
        if not self.frames:
            return b''
        
        # Create temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            wf = wave.open(temp_file.name, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            
            # Read back as bytes
            with open(temp_file.name, 'rb') as f:
                audio_bytes = f.read()
            
            os.unlink(temp_file.name)
            return audio_bytes
    
    def cleanup(self):
        """Cleanup audio resources"""
        self.audio.terminate()

class AudioPlayer:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
    
    def play_audio(self, audio_bytes: bytes):
        """Play audio from bytes"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            # Open and play the audio file
            wf = wave.open(temp_file_path, 'rb')
            
            stream = self.audio.open(
                format=self.audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
            
            print("🔊 Playing audio response...")
            
            # Play audio
            data = wf.readframes(1024)
            while data:
                stream.write(data)
                data = wf.readframes(1024)
            
            stream.stop_stream()
            stream.close()
            wf.close()
            
            os.unlink(temp_file_path)
            print("✅ Audio playback complete")
            
        except Exception as e:
            print(f"❌ Audio playback error: {e}")
    
    def cleanup(self):
        """Cleanup audio resources"""
        self.audio.terminate()

class VoiceAgentDemo:
    def __init__(self):
        self.db = None
        self.current_product = None
        self.store_id = "store_001"  # Walmart MG Road
        self.recorder = AudioRecorder()
        self.player = AudioPlayer()
        
    async def initialize(self):
        """Initialize database connection and load demo product"""
        await connect_to_mongo()
        self.db = get_database()
        
        # Load a demo product (Amul Butter from Walmart)
        self.current_product = await self.db.products.find_one({
            "_id": "prod_001",
            "store_id": self.store_id
        })
        
        if not self.current_product:
            raise Exception("Demo product not found. Please run populate_db.py first.")

    async def voice_interaction_demo(self):
        """Interactive voice demo with real audio input/output"""
        
        print("\n🎙️ INTERACTIVE VOICE DEMO")
        print("=" * 50)
        print(f"Store: Walmart MG Road")
        print(f"Current Product: {self.current_product['name']} by {self.current_product['brand']}")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. Voice Query (Record your question)")
            print("2. Text Query (Type your question)")
            print("3. Exit")
            
            choice = input("\nSelect option (1-3): ").strip()
            
            if choice == "1":
                await self._handle_voice_query()
            elif choice == "2":
                await self._handle_text_query()
            elif choice == "3":
                break
            else:
                print("Invalid option. Please try again.")
    
    async def _handle_voice_query(self):
        """Handle voice input query"""
        try:
            print("\n🎤 Voice Query Mode")
            print("-" * 20)
            
            # Step 1: Record audio
            audio_bytes = self.recorder.start_recording()
            
            if not audio_bytes:
                print("❌ No audio recorded")
                return
            
            print("📝 Processing speech-to-text...")
            
            # Step 2: STT - Transcribe audio
            transcription = await transcribe_audio(audio_bytes)
            print(f"🎤 You said: \"{transcription}\"")
            
            if not transcription or transcription.strip() == "Sorry, I couldn't understand what you said.":
                print("❌ Could not understand audio. Please try again.")
                return
            
            # Step 3: Process with LLM and TTS
            await self._process_query_with_audio(transcription)
            
        except Exception as e:
            print(f"❌ Voice query error: {e}")
    
    async def _handle_text_query(self):
        """Handle text input query"""
        try:
            print("\n📝 Text Query Mode")
            print("-" * 20)
            
            query = input("Enter your question: ").strip()
            
            if not query:
                print("❌ Empty query")
                return
            
            print(f"📝 Your question: \"{query}\"")
            
            # Process with LLM and TTS
            await self._process_query_with_audio(query)
            
        except Exception as e:
            print(f"❌ Text query error: {e}")
    
    async def _process_query_with_audio(self, query: str):
        """Process query and generate audio response"""
        try:
            # Get product context
            product_context = await get_product_context(self.current_product["_id"])
            
            print("🤖 AI Processing...")
            
            # Step 3: LLM - Process query
            response_text = await process_query(
                query,
                product_context,
                self.store_id
            )
            
            print(f"💬 Agent Response: \"{response_text}\"")
            
            # Step 4: TTS - Generate speech
            print("🔊 Generating audio response...")
            audio_bytes = await generate_speech(response_text)
            
            # Step 5: Play audio
            self.player.play_audio(audio_bytes)
            
        except Exception as e:
            print(f"❌ Query processing error: {e}")

    async def streaming_voice_demo(self):
        """Demo streaming interaction with real audio"""
        
        print("\n🌊 STREAMING VOICE DEMO")
        print("=" * 50)
        
        print("This will record your question and stream the response...")
        
        # Record audio
        audio_bytes = self.recorder.start_recording()
        
        if not audio_bytes:
            print("❌ No audio recorded")
            return
        
        # Transcribe
        print("📝 Processing speech-to-text...")
        customer_query = await transcribe_audio(audio_bytes)
        print(f"🎤 You said: \"{customer_query}\"")
        
        if not customer_query or customer_query.strip() == "Sorry, I couldn't understand what you said.":
            print("❌ Could not understand audio")
            return
        
        # Get product context
        product_context = await get_product_context(self.current_product["_id"])
        
        print("\n🤖 Agent (streaming response):")
        print("💬 ", end="", flush=True)
        
        full_response = ""
        async for chunk in process_query_streaming(
            customer_query,
            product_context,
            self.store_id
        ):
            print(chunk, end=" ", flush=True)
            full_response += chunk + " "
            await asyncio.sleep(0.3)
        
        print(f"\n\n🔊 Generating audio for: \"{full_response.strip()}\"")
        
        # Generate and play audio
        audio_bytes = await generate_speech(full_response.strip())
        self.player.play_audio(audio_bytes)

    async def simulate_customer_queries(self):
        """Simulate various customer queries about the product"""
        
        print("🛒 VOICE AGENT DEMO - RETAIL ASSISTANT")
        print("=" * 50)
        print(f"Store: Walmart MG Road")
        print(f"Current Product: {self.current_product['name']} by {self.current_product['brand']}")
        print(f"Location: {self.current_product['shelf_location']}")
        print("=" * 50)
        
        # Demo scenarios
        scenarios = [
            {
                "customer_query": "What's the price of this butter?",
                "description": "Price inquiry"
            },
            {
                "customer_query": "What ingredients are in this Amul butter?",
                "description": "Ingredient check"
            },
            {
                "customer_query": "Where can I find this product in the store?",
                "description": "Location query"
            },
            {
                "customer_query": "How many units do you have in stock?",
                "description": "Stock availability"
            },
            {
                "customer_query": "Do you have any other butter brands available?",
                "description": "Alternative products"
            },
            {
                "customer_query": "Is this butter good for baking?",
                "description": "Usage recommendation"
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n🎯 SCENARIO {i}: {scenario['description']}")
            print("-" * 30)
            
            await self._process_voice_interaction(scenario['customer_query'])
            
            # Pause between scenarios
            print("\n" + "⏳ Processing..." + "\n")
            await asyncio.sleep(1)
    
    async def _process_voice_interaction(self, customer_query: str):
        """Simulate complete voice interaction pipeline"""
        
        # Step 1: Simulate STT (Speech-to-Text)
        print(f"🎤 Customer says: \"{customer_query}\"")
        print("📝 STT Transcription: ✅ Success")
        
        # Step 2: Get product context
        product_context = {
            "name": self.current_product["name"],
            "brand": self.current_product["brand"],
            "price": self.current_product["price"],
            "ingredients": self.current_product["ingredients"],
            "shelf_location": self.current_product["shelf_location"],
            "stock": self.current_product["stock"]
        }
        
        # Step 3: Process with LLM
        print("🤖 AI Processing...")
        response_text = await process_query(
            customer_query,
            product_context,
            self.store_id
        )
        
        print(f"💬 Agent Response: \"{response_text}\"")
        
        # Step 4: Simulate TTS (Text-to-Speech)
        print("🔊 TTS Generation: ✅ Audio ready for playback")
        
        # Optional: Generate actual audio (commented out for demo)
        # audio_bytes = await generate_speech(response_text)
        # print(f"📱 Audio generated: {len(audio_bytes)} bytes")
        
    async def product_comparison_demo(self):
        """Demo product comparison scenario"""
        
        print("\n" * 2)
        print("🔍 PRODUCT COMPARISON DEMO")
        print("=" * 50)
        
        # Get another butter product from different store for comparison
        other_product = await self.db.products.find_one({
            "_id": "prod_006",  # Amul Butter from Big Bazaar
            "store_id": "store_002"
        })
        
        if other_product:
            print(f"Current Store: {self.current_product['name']} - ₹{self.current_product['price']}")
            print(f"Other Store: {other_product['name']} - ₹{other_product['price']}")
            
            customer_query = "Is this butter cheaper here compared to other stores?"
            
            print(f"\n🎤 Customer: \"{customer_query}\"")
            
            # Enhanced context with comparison data
            enhanced_context = {
                "name": self.current_product["name"],
                "brand": self.current_product["brand"],
                "price": self.current_product["price"],
                "ingredients": self.current_product["ingredients"],
                "shelf_location": self.current_product["shelf_location"],
                "stock": self.current_product["stock"],
                "comparison_price": other_product["price"],
                "comparison_store": "Big Bazaar Forum Mall"
            }
            
            response = await process_query(
                customer_query,
                enhanced_context,
                self.store_id
            )
            
            print(f"💬 Agent: \"{response}\"")
    
    async def run_demo(self):
        """Run complete demo with audio capabilities"""
        try:
            await self.initialize()
            
            print("🛒 VOICE AGENT DEMO - RETAIL ASSISTANT")
            print("=" * 50)
            print("This demo includes real audio input/output capabilities!")
            print("Make sure you have a microphone connected.")
            print("=" * 50)
            
            while True:
                print("\nDemo Options:")
                print("1. Interactive Voice Demo (Real Audio I/O)")
                print("2. Streaming Voice Demo")
                print("3. Simulated Scenarios (Text-based)")
                print("4. Product Comparison Demo")
                print("5. Exit")
                
                choice = input("\nSelect demo (1-5): ").strip()
                
                if choice == "1":
                    await self.voice_interaction_demo()
                elif choice == "2":
                    await self.streaming_voice_demo()
                elif choice == "3":
                    await self.simulate_customer_queries()
                elif choice == "4":
                    await self.product_comparison_demo()
                elif choice == "5":
                    break
                else:
                    print("Invalid option. Please try again.")
            
            print("\n🎉 DEMO COMPLETE!")
            print("Thanks for testing the Voice Agent!")
            
        except Exception as e:
            print(f"❌ Demo error: {e}")
        finally:
            self.recorder.cleanup()
            self.player.cleanup()
            await close_mongo_connection()

async def main():
    """Main demo runner"""
    demo = VoiceAgentDemo()
    await demo.run_demo()

if __name__ == "__main__":
    print("Starting Voice Agent Demo with Real Audio...")
    print("Note: Make sure you have pyaudio installed: pip install pyaudio")
    asyncio.run(main())
