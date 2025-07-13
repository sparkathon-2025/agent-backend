from fastapi import APIRouter, Depends, HTTPException, status
from models.schemas import ProductScan, Product, User
from routers.auth import get_current_user
from db.mongo import get_database
from services.product_query import (
    get_product_variants,
    get_product_comparison_tags,
    get_product_shelf_location,
    find_similar_products
)

router = APIRouter()

@router.post("/scan", response_model=Product)
async def scan_product(scan_data: ProductScan, current_user: User = Depends(get_current_user)):
    db = get_database()
    
    if not current_user.current_store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please connect to a store first"
        )
    
    # Find product by barcode_id in current store
    product = await db.products.find_one({
        "product_code": scan_data.barcode_id,
        "store_id": current_user.current_store_id
    })
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in this store"
        )
    
    return Product(**product, id=product["_id"])

@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: str):
    db = get_database()
    
    product = await db.products.find_one({"_id": product_id})
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return Product(**product, id=product["_id"])

@router.get("/store/{store_id}")
async def list_store_products(store_id: str):
    """List all products in a store"""
    db = get_database()
    products = await db.products.find({"store_id": store_id}).to_list(length=None)
    return [Product(**product, id=product["_id"]) for product in products]

@router.get("/{product_id}/variants")
async def get_product_variants_info(product_id: str):
    """Get product variants information"""
    result = await get_product_variants(product_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return result

@router.get("/{product_id}/comparison-tags")
async def get_product_comparison_info(product_id: str):
    """Get product comparison tags"""
    result = await get_product_comparison_tags(product_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return result

@router.get("/{product_id}/shelf-location")
async def get_product_location_info(product_id: str):
    """Get product shelf location"""
    result = await get_product_shelf_location(product_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return result

@router.get("/{product_id}/similar")
async def get_similar_products_info(product_id: str, current_user: User = Depends(get_current_user)):
    """Find similar products in user's current store"""
    if not current_user.current_store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please connect to a store first"
        )
    
    result = await find_similar_products(product_id, current_user.current_store_id)
    return {"similar_products": result}
