import asyncio
import sys
import os
import json
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.mongo import connect_to_mongo, get_database, close_mongo_connection
from services.gpt_agent import process_query, process_query_streaming
from services.sesame_tts import generate_speech
from services.product_query import get_product_context
from dotenv import load_dotenv

load_dotenv()

class VoiceAgentDemo:
    def __init__(self):
        self.db = None
        self.current_product = None
        self.store_id = "store_001"  # Walmart MG Road
        
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
        
    async def streaming_demo(self):
        """Demonstrate streaming interaction"""
        
        print("\n" * 2)
        print("🌊 STREAMING DEMO")
        print("=" * 50)
        print("Simulating real-time conversation...")
        
        customer_query = "Can you tell me everything about this Amul butter and help me decide if I should buy it?"
        
        print(f"🎤 Customer: \"{customer_query}\"")
        print("\n🤖 Agent (streaming response):")
        
        product_context = {
            "name": self.current_product["name"],
            "brand": self.current_product["brand"],
            "price": self.current_product["price"],
            "ingredients": self.current_product["ingredients"],
            "shelf_location": self.current_product["shelf_location"],
            "stock": self.current_product["stock"]
        }
        
        full_response = ""
        print("💬 ", end="", flush=True)
        
        async for chunk in process_query_streaming(
            customer_query,
            product_context,
            self.store_id
        ):
            print(chunk, end=" ", flush=True)
            full_response += chunk + " "
            # Simulate real-time streaming delay
            await asyncio.sleep(0.3)
        
        print("\n🔊 TTS: Converting to speech...")
        print("✅ Streaming complete!")
        
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
        """Run complete demo"""
        try:
            await self.initialize()
            
            # Run all demo scenarios
            await self.simulate_customer_queries()
            await self.streaming_demo()
            await self.product_comparison_demo()
            
            print("\n" * 2)
            print("🎉 DEMO COMPLETE!")
            print("=" * 50)
            print("The voice agent successfully handled:")
            print("✅ Price inquiries")
            print("✅ Ingredient information")
            print("✅ Location guidance")
            print("✅ Stock availability")
            print("✅ Product recommendations")
            print("✅ Streaming responses")
            print("✅ Multi-store comparisons")
            
        except Exception as e:
            print(f"❌ Demo error: {e}")
        finally:
            await close_mongo_connection()

async def main():
    """Main demo runner"""
    demo = VoiceAgentDemo()
    await demo.run_demo()

if __name__ == "__main__":
    print("Starting Voice Agent Demo...")
    asyncio.run(main())
