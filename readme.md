# Voice Agent Backend

FastAPI-based backend for a voice-based retail assistant used in physical stores.

## Features

🧴 **Product Information** - Get details about ingredients, size, brand  
📦 **Availability Check** - Check stock and variants  
🔄 **Product Comparison** - Compare with similar products  
🧭 **Store Navigation** - Find aisle/shelf locations  
🗣️ **Voice Interaction** - Natural speech processing with local Whisper v3 Turbo STT, LLM, and TTS

## Tech Stack

- **API**: FastAPI
- **Database**: MongoDB with Motor (async)
- **STT**: Local Whisper v3 Turbo (offline)
- **LLM**: OpenAI GPT-4
- **TTS**: Sesame TTS API

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -e .
   ```

2. **Setup environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the server**:
   ```bash
   python main.py
   ```

4. **API Documentation**: Visit `http://localhost:8000/docs`

## API Endpoints

### Store Management
- `POST /store/connect` - Connect to store via QR
- `GET /store/{store_id}` - Get store details
- `GET /store/` - List all stores

### Product Management
- `POST /product/scan` - Scan product barcode
- `GET /product/{id}` - Get product details
- `GET /product/store/{store_id}` - List products in store

### Voice Agent (Main MVP)
- `POST /voice-agent/query` - Process voice input and return audio response
- `WebSocket /voice-agent/stream` - Real-time voice interaction

## Usage Flow

1. Connect to a store by providing store_id
2. Optionally scan product barcode for context
3. Speak to voice agent
4. Backend processes: Audio → STT → LLM → TTS → Audio response

## Environment Variables

```bash
# MongoDB
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=voice_agent

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Sesame (for TTS)
SESAME_TTS_API_URL=https://api.sesame.com/v1/tts
SESAME_API_KEY=your-sesame-api-key

# Deepgram (for STT)
DEEPGRAM_API_KEY=your-deepgram-api-key
```

## Database Schema

### Stores Collection
```json
{
  "_id": "store123",
  "name": "Walmart MG Road",
  "location": "Bangalore"
}
```

### Products Collection
```json
{
  "_id": "prod987",
  "store_id": "store123",
  "product_code": "XYZ123",
  "name": "Amul Butter",
  "brand": "Amul",
  "ingredients": "Pasteurized cream, salt",
  "price": 55,
  "stock": 20,
  "variants": ["100g", "500g"],
  "comparison_tags": ["butter", "dairy"],
  "shelf_location": "Aisle 4, Left"
}
```

## Development

The project follows a modular structure:

- `routers/` - API route handlers
- `services/` - Business logic and external API integrations
- `models/` - Pydantic schemas
- `db/` - Database connection and operations

## Deployment

Ready for deployment on Railway, Render, or AWS EC2. Make sure to:

1. Set environment variables
2. Configure MongoDB connection
3. Add domain to CORS origins
4. Setup SSL certificates for production

## Documentation

Comprehensive documentation is available in the `docs/` directory, including:

- API reference
- Setup and installation guide
- Usage examples
- Contribution guidelines

1. Set environment variables
2. Configure MongoDB connection
3. Add domain to CORS origins
4. Setup SSL certificates for production

## Documentation

Comprehensive documentation is available in the `docs/` directory, including:

- API reference
- Setup and installation guide
- Usage examples
- Contribution guidelines
- Setup and installation guide
- Usage examples
- Contribution guidelines

