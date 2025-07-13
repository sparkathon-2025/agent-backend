import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.mongo import connect_to_mongo, get_database, close_mongo_connection
from dotenv import load_dotenv

load_dotenv()

async def populate_database():
    """Populate database with sample stores and products"""
    
    await connect_to_mongo()
    db = get_database()
    
    # Clear existing data
    await db.stores.delete_many({})
    await db.products.delete_many({})
    
    # Sample stores
    stores = [
        {
            "_id": "store_001",
            "name": "Walmart MG Road",
            "location": "Bangalore, Karnataka"
        },
        {
            "_id": "store_002", 
            "name": "Big Bazaar Forum Mall",
            "location": "Bangalore, Karnataka"
        },
        {
            "_id": "store_003",
            "name": "Spencer's Richmond Road",
            "location": "Bangalore, Karnataka"
        }
    ]
    
    # Insert stores
    await db.stores.insert_many(stores)
    print(f"Inserted {len(stores)} stores")
    
    # Sample products for each store
    products = [
        # Store 1 - Walmart MG Road
        {
            "_id": "prod_001",
            "store_id": "store_001",
            "product_code": "8901030875224",
            "name": "Amul Butter",
            "brand": "Amul",
            "ingredients": "Pasteurized cream, salt",
            "price": 55.0,
            "stock": 25,
            "variants": ["100g", "500g"],
            "comparison_tags": ["butter", "dairy", "spread"],
            "shelf_location": "Aisle 4, Left Side, Shelf 2"
        },
        {
            "_id": "prod_002",
            "store_id": "store_001",
            "product_code": "8901030840047",
            "name": "Amul Milk",
            "brand": "Amul",
            "ingredients": "Full cream milk",
            "price": 28.0,
            "stock": 40,
            "variants": ["500ml", "1L"],
            "comparison_tags": ["milk", "dairy", "beverage"],
            "shelf_location": "Dairy Section, Fridge 1"
        },
        {
            "_id": "prod_003",
            "store_id": "store_001",
            "product_code": "8901030875231",
            "name": "Britannia Good Day Cookies",
            "brand": "Britannia",
            "ingredients": "Wheat flour, sugar, vegetable oil, milk solids",
            "price": 20.0,
            "stock": 60,
            "variants": ["75g", "150g", "300g"],
            "comparison_tags": ["cookies", "biscuits", "snacks"],
            "shelf_location": "Aisle 2, Right Side, Shelf 3"
        },
        {
            "_id": "prod_004",
            "store_id": "store_001",
            "product_code": "8901030874578",
            "name": "Maggi 2-Minute Noodles",
            "brand": "Nestle",
            "ingredients": "Wheat flour, palm oil, salt, spices",
            "price": 14.0,
            "stock": 80,
            "variants": ["70g", "140g", "420g Family Pack"],
            "comparison_tags": ["noodles", "instant food", "snacks"],
            "shelf_location": "Aisle 3, Center, Shelf 1"
        },
        {
            "_id": "prod_005",
            "store_id": "store_001",
            "product_code": "8901030875248",
            "name": "Colgate Total Toothpaste",
            "brand": "Colgate",
            "ingredients": "Sodium fluoride, triclosan, sorbitol",
            "price": 85.0,
            "stock": 35,
            "variants": ["100g", "200g"],
            "comparison_tags": ["toothpaste", "oral care", "hygiene"],
            "shelf_location": "Personal Care, Aisle 7, Left"
        },
        
        # Store 2 - Big Bazaar Forum Mall
        {
            "_id": "prod_006",
            "store_id": "store_002",
            "product_code": "8901030875224",
            "name": "Amul Butter",
            "brand": "Amul",
            "ingredients": "Pasteurized cream, salt",
            "price": 58.0,
            "stock": 20,
            "variants": ["100g", "500g"],
            "comparison_tags": ["butter", "dairy", "spread"],
            "shelf_location": "Dairy Corner, Section B"
        },
        {
            "_id": "prod_007",
            "store_id": "store_002",
            "product_code": "8901030840054",
            "name": "Mother Dairy Milk",
            "brand": "Mother Dairy",
            "ingredients": "Toned milk",
            "price": 26.0,
            "stock": 50,
            "variants": ["500ml", "1L"],
            "comparison_tags": ["milk", "dairy", "beverage"],
            "shelf_location": "Cold Storage, Section A"
        },
        {
            "_id": "prod_008",
            "store_id": "store_002",
            "product_code": "8901030875255",
            "name": "Parle-G Biscuits",
            "brand": "Parle",
            "ingredients": "Wheat flour, sugar, vegetable oil",
            "price": 10.0,
            "stock": 100,
            "variants": ["50g", "100g", "200g"],
            "comparison_tags": ["biscuits", "cookies", "snacks"],
            "shelf_location": "Snacks Aisle, Row 2"
        },
        {
            "_id": "prod_009",
            "store_id": "store_002",
            "product_code": "8901030875262",
            "name": "Tata Salt",
            "brand": "Tata",
            "ingredients": "Iodized salt",
            "price": 22.0,
            "stock": 45,
            "variants": ["1kg", "2kg"],
            "comparison_tags": ["salt", "spices", "cooking"],
            "shelf_location": "Grocery Section, Shelf 4"
        },
        
        # Store 3 - Spencer's Richmond Road
        {
            "_id": "prod_010",
            "store_id": "store_003",
            "product_code": "8901030875279",
            "name": "Dabur Honey",
            "brand": "Dabur",
            "ingredients": "Pure honey",
            "price": 150.0,
            "stock": 15,
            "variants": ["250g", "500g", "1kg"],
            "comparison_tags": ["honey", "natural", "sweetener"],
            "shelf_location": "Health Food Section, Top Shelf"
        },
        {
            "_id": "prod_011",
            "store_id": "store_003",
            "product_code": "8901030875286",
            "name": "Lays Potato Chips",
            "brand": "Lays",
            "ingredients": "Potatoes, vegetable oil, salt",
            "price": 20.0,
            "stock": 75,
            "variants": ["25g", "50g", "90g"],
            "comparison_tags": ["chips", "snacks", "potato"],
            "shelf_location": "Snacks Corner, Eye Level"
        },
        {
            "_id": "prod_012",
            "store_id": "store_003",
            "product_code": "8901030875293",
            "name": "Red Label Tea",
            "brand": "Brooke Bond",
            "ingredients": "Black tea",
            "price": 95.0,
            "stock": 30,
            "variants": ["250g", "500g", "1kg"],
            "comparison_tags": ["tea", "beverage", "black tea"],
            "shelf_location": "Beverages, Aisle 1"
        }
    ]
    
    # Insert products
    await db.products.insert_many(products)
    print(f"Inserted {len(products)} products")
    
    # Print summary
    print("\n=== Database Population Complete ===")
    print(f"Stores: {len(stores)}")
    print(f"Products: {len(products)}")
    
    for store in stores:
        store_products = [p for p in products if p["store_id"] == store["_id"]]
        print(f"  {store['name']}: {len(store_products)} products")
    
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(populate_database())
