from fastapi import APIRouter, Depends, HTTPException, status
from models.schemas import ProductScan, Product, User
from routers.auth import get_current_user
from db.mongo import get_database

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
