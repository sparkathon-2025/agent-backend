from fastapi import APIRouter, HTTPException, status
from services.product_query import (
    get_product_info,
    get_product_variants,
    get_product_comparison_tags,
    get_product_shelf_location,
    find_similar_products
)

router = APIRouter()

@router.get("/product/{product_id}/info")
async def query_product_info(product_id: str):
    """Get basic product information for tools/LLM"""
    result = await get_product_info(product_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return result

@router.get("/product/{product_id}/variants")
async def query_product_variants(product_id: str):
    """Get product variants information"""
    result = await get_product_variants(product_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return result

@router.get("/product/{product_id}/comparison-tags")
async def query_product_comparison_tags(product_id: str):
    """Get product comparison tags"""
    result = await get_product_comparison_tags(product_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return result

@router.get("/product/{product_id}/shelf-location")
async def query_product_shelf_location(product_id: str):
    """Get product shelf location"""
    result = await get_product_shelf_location(product_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return result

@router.get("/product/{product_id}/similar/{store_id}")
async def query_similar_products(product_id: str, store_id: str):
    """Find similar products in the same store"""
    result = await find_similar_products(product_id, store_id)
    return {"similar_products": result}
