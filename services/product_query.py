from db.mongo import get_database
from typing import Optional, Dict

async def get_product_context(product_id: str) -> Optional[Dict]:
    """Get product information for LLM context"""
    
    db = get_database()
    product = await db.products.find_one({"_id": product_id})
    
    if not product:
        return None
    
    return {
        "id": product["_id"],
        "name": product["name"],
        "brand": product["brand"],
        "price": product["price"],
        "ingredients": product["ingredients"],
        "stock": product["stock"],
        "variants": product["variants"],
        "shelf_location": product["shelf_location"],
        "comparison_tags": product["comparison_tags"]
    }
