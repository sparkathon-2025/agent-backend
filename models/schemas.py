from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str
    email: str
    current_store_id: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

# Store schemas
class StoreConnect(BaseModel):
    store_id: str

class Store(BaseModel):
    id: str
    name: str
    location: str

# Product schemas
class ProductScan(BaseModel):
    barcode_id: str

class Product(BaseModel):
    id: str
    store_id: str
    product_code: str
    name: str
    brand: str
    ingredients: str
    price: float
    stock: int
    variants: List[str]
    comparison_tags: List[str]
    shelf_location: str

# Voice Agent schemas
class VoiceQuery(BaseModel):
    user_id: str
    product_id: Optional[str] = None

class VoiceResponse(BaseModel):
    text: str
    audio: str  # base64 encoded audio
