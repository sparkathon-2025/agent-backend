# Voice Agent Demo

This directory contains demonstration scripts for the Voice Agent system.

## Prerequisites

1. Ensure MongoDB is running
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env`
4. Populate database: `python scripts/populate_db.py`

## Available Demos

### 1. Automated Demo (`voice_agent_demo.py`)

Runs pre-defined scenarios demonstrating the complete voice agent pipeline:

```bash
cd /mnt/d/projects/agent-backend
python demo/voice_agent_demo.py
```

**Features:**
- Price inquiries
- Ingredient information  
- Location guidance
- Stock availability
- Product recommendations
- Streaming responses
- Multi-store comparisons

### 2. Interactive Demo (`interactive_demo.py`)

Interactive chat where you can ask questions about products:

```bash
cd /mnt/d/projects/agent-backend  
python demo/interactive_demo.py
```

**Features:**
- Select from available products
- Ask natural language questions
- Get real-time AI responses
- Switch between products

## Sample Interactions

### Price Query
```
🎤 You: What's the price of this butter?
🤖 Agent: This Amul Butter costs ₹55.0 and we have 25 units in stock.
```

### Location Query  
```
🎤 You: Where can I find this product?
🤖 Agent: You can find this product at Aisle 4, Left Side, Shelf 2.
```

### Ingredient Query
```
🎤 You: What ingredients are in this?
🤖 Agent: This Amul Butter contains pasteurized cream and salt.
```

## Demo Product Data

The demos use real product data including:
- **Amul Butter** (₹55) - Aisle 4, Left Side, Shelf 2
- **Amul Milk** (₹28) - Dairy Section, Fridge 1  
- **Britannia Cookies** (₹20) - Aisle 2, Right Side, Shelf 3
- **Maggi Noodles** (₹14) - Aisle 3, Center, Shelf 1
- **Colgate Toothpaste** (₹85) - Personal Care, Aisle 7

## Architecture Demonstrated

```
Voice Input → STT (Whisper) → LLM (GPT) → TTS (Sesame) → Voice Output
                ↓
         Product Database Query
```

## Notes

- TTS audio generation is simulated in demos (actual audio can be enabled)
- Real-time streaming demonstrates production capabilities
- Product context is dynamically loaded from MongoDB
- Multi-store price comparison showcases advanced features
