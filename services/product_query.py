from db.mongo import get_database
from typing import Optional, Dict, List

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

async def get_product_info(product_id: str) -> Optional[Dict]:
    """Get basic product information"""
    db = get_database()
    product = await db.products.find_one({"_id": product_id})
    
    if not product:
        return None
    
    return {
        "id": product["_id"],
        "name": product["name"],
        "brand": product["brand"],
        "price": product["price"],
        "stock": product["stock"],
        "store_id": product["store_id"]
    }

async def get_product_variants(product_id: str) -> Optional[Dict]:
    """Get product variants information"""
    db = get_database()
    product = await db.products.find_one({"_id": product_id})
    
    if not product:
        return None
    
    return {
        "id": product["_id"],
        "name": product["name"],
        "variants": product["variants"]
    }

async def get_product_comparison_tags(product_id: str) -> Optional[Dict]:
    """Get product comparison tags for finding similar products"""
    db = get_database()
    product = await db.products.find_one({"_id": product_id})
    
    if not product:
        return None
    
    return {
        "id": product["_id"],
        "name": product["name"],
        "comparison_tags": product["comparison_tags"],
        "brand": product["brand"]
    }

async def get_product_shelf_location(product_id: str) -> Optional[Dict]:
    """Get product shelf location information"""
    db = get_database()
    product = await db.products.find_one({"_id": product_id})
    
    if not product:
        return None
    
    return {
        "id": product["_id"],
        "name": product["name"],
        "shelf_location": product["shelf_location"],
        "store_id": product["store_id"]
    }

async def find_similar_products(product_id: str, store_id: str) -> List[Dict]:
    """Find products with similar comparison tags in the same store"""
    db = get_database()
    
    # Get the original product's comparison tags
    product = await db.products.find_one({"_id": product_id})
    if not product:
        return []
    
    comparison_tags = product.get("comparison_tags", [])
    if not comparison_tags:
        return []
    
    # Find products with overlapping tags
    similar_products = await db.products.find({
        "store_id": store_id,
        "_id": {"$ne": product_id},
        "comparison_tags": {"$in": comparison_tags}
    }).to_list(length=10)  # Limit to 10 results
    
    return [
        {
            "id": p["_id"],
            "name": p["name"],
            "brand": p["brand"],
            "price": p["price"],
            "comparison_tags": p["comparison_tags"]
        }
        for p in similar_products
    ]
