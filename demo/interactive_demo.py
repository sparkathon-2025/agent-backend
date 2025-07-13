import asyncio
import sys
import os
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.mongo import connect_to_mongo, get_database, close_mongo_connection
from services.gpt_agent import process_query
from dotenv import load_dotenv

load_dotenv()

class InteractiveDemo:
    def __init__(self):
        self.db = None
        self.current_product = None
        self.store_id = "store_001"
        self.products = []
        
    async def initialize(self):
        """Initialize demo environment"""
        await connect_to_mongo()
        self.db = get_database()
        
        # Load all products from store
        cursor = self.db.products.find({"store_id": self.store_id})
        self.products = await cursor.to_list(length=None)
        
        if not self.products:
            raise Exception("No products found. Run populate_db.py first.")
    
    def display_products(self):
        """Display available products"""
        print("\n📦 AVAILABLE PRODUCTS:")
        print("-" * 40)
        for i, product in enumerate(self.products, 1):
            print(f"{i}. {product['name']} by {product['brand']} - ₹{product['price']}")
        print("-" * 40)
    
    def select_product(self) -> Optional[dict]:
        """Let user select a product"""
        self.display_products()
        
        while True:
            try:
                choice = input(f"\nSelect product (1-{len(self.products)}) or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                idx = int(choice) - 1
                if 0 <= idx < len(self.products):
                    return self.products[idx]
                else:
                    print("Invalid selection. Please try again.")
                    
            except ValueError:
                print("Please enter a valid number.")
    
    async def chat_with_agent(self, product: dict):
        """Interactive chat session"""
        product_context = {
            "name": product["name"],
            "brand": product["brand"],
            "price": product["price"],
            "ingredients": product["ingredients"],
            "shelf_location": product["shelf_location"],
            "stock": product["stock"]
        }
        
        print(f"\n🤖 VOICE AGENT - Now helping with {product['name']}")
        print("Type your questions or 'back' to change product, 'quit' to exit")
        print("-" * 60)
        
        while True:
            user_input = input("\n🎤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                return False
            
            if user_input.lower() in ['back', 'change']:
                return True
            
            if not user_input:
                continue
            
            # Process query
            print("🤖 Agent: ", end="", flush=True)
            
            try:
                response = await process_query(
                    user_input,
                    product_context,
                    self.store_id
                )
                print(response)
                
            except Exception as e:
                print(f"Sorry, I encountered an error: {e}")
    
    async def run_interactive_demo(self):
        """Run interactive demo"""
        try:
            await self.initialize()
            
            print("🛒 INTERACTIVE VOICE AGENT DEMO")
            print("=" * 50)
            print("Welcome to Walmart MG Road!")
            print("I'm your AI shopping assistant.")
            
            while True:
                product = self.select_product()
                
                if product is None:
                    break
                
                continue_demo = await self.chat_with_agent(product)
                
                if not continue_demo:
                    break
            
            print("\n👋 Thanks for trying the Voice Agent Demo!")
            
        except Exception as e:
            print(f"❌ Demo error: {e}")
        finally:
            await close_mongo_connection()

if __name__ == "__main__":
    demo = InteractiveDemo()
    asyncio.run(demo.run_interactive_demo())
