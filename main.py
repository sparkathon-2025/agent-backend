from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import store, product, voice_agent
from db.mongo import connect_to_mongo, close_mongo_connection
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Voice Agent Backend",
    description="FastAPI backend for voice-based retail assistant",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
#app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(store.router, prefix="/store", tags=["store"])
app.include_router(product.router, prefix="/product", tags=["product"])
app.include_router(voice_agent.router, prefix="/voice-agent", tags=["voice-agent"])

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {"message": "Voice Agent Backend API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "voice-agent-backend"}

if __name__ == "__main__":
    import uvicorn
    # Use PORT from environment variable for Render deployment
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
