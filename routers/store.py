from fastapi import APIRouter, Depends, HTTPException, status
from models.schemas import StoreConnect, Store, User
from routers.auth import get_current_user
from db.mongo import get_database

router = APIRouter()

@router.post("/connect")
async def connect_store(store_data: StoreConnect, current_user: User = Depends(get_current_user)):
    db = get_database()
    
    # Verify store exists
    store = await db.stores.find_one({"_id": store_data.store_id})
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    # Update user's current store
    await db.users.update_one(
        {"_id": current_user.id},
        {"$set": {"current_store_id": store_data.store_id}}
    )
    
    return {"message": "Connected to store successfully", "store_id": store_data.store_id}

@router.get("/{store_id}", response_model=Store)
async def get_store(store_id: str):
    db = get_database()
    
    store = await db.stores.find_one({"_id": store_id})
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    return Store(
        id=store["_id"],
        name=store["name"],
        location=store["location"]
    )

@router.get("/")
async def list_stores():
    """List all available stores"""
    db = get_database()
    stores = await db.stores.find({}).to_list(length=None)
    return [Store(id=store["_id"], name=store["name"], location=store["location"]) for store in stores]
