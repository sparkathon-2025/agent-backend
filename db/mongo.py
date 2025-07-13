from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
import os
from typing import Optional

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database = None

db = MongoDB()

async def connect_to_mongo():
    """Create database connection"""
    db.client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db.database = db.client[os.getenv("DATABASE_NAME")]
    
    # Create indexes
    await db.database.users.create_index("email", unique=True)
    await db.database.products.create_index([("store_id", 1), ("product_code", 1)])

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()

def get_database():
    return db.database
