import openai
import os
from typing import Optional, Dict, AsyncGenerator

openai.api_key = os.getenv("OPENAI_API_KEY")

async def process_query(
    user_query: str, 
    product_context: Optional[Dict] = None,
    store_id: Optional[str] = None
) -> str:
    """Process user query using GPT with product context"""
    
    # Build system prompt
    system_prompt = """You are a helpful retail assistant in a physical store. 
    Answer customer questions about products, availability, comparisons, and store navigation.
    Keep responses concise and friendly. If you don't have specific information, say so politely."""
    
    # Build context
    context_parts = []
    if product_context:
        context_parts.append(f"Current product: {product_context['name']} by {product_context['brand']}")
        context_parts.append(f"Price: ${product_context['price']}")
        context_parts.append(f"Ingredients: {product_context['ingredients']}")
        context_parts.append(f"Location: {product_context['shelf_location']}")
        context_parts.append(f"Stock: {product_context['stock']} units available")
    
    if store_id:
        context_parts.append(f"Store ID: {store_id}")
    
    context_text = "\n".join(context_parts) if context_parts else "No specific product context available."
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context_text}\n\nCustomer question: {user_query}"}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"GPT Error: {e}")
        return "I'm sorry, I'm having trouble processing your request right now. Please try again."

async def process_query_streaming(
    user_query: str, 
    product_context: Optional[Dict] = None,
    store_id: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """Process user query using GPT with streaming response"""
    
    # Build system prompt
    system_prompt = """You are a helpful retail assistant in a physical store. 
    Answer customer questions about products, availability, comparisons, and store navigation.
    Keep responses concise and friendly. If you don't have specific information, say so politely.
    Provide responses that can be spoken naturally in real-time."""
    
    # Build context
    context_parts = []
    if product_context:
        context_parts.append(f"Current product: {product_context['name']} by {product_context['brand']}")
        context_parts.append(f"Price: ${product_context['price']}")
        context_parts.append(f"Ingredients: {product_context['ingredients']}")
        context_parts.append(f"Location: {product_context['shelf_location']}")
        context_parts.append(f"Stock: {product_context['stock']} units available")
    
    if store_id:
        context_parts.append(f"Store ID: {store_id}")
    
    context_text = "\n".join(context_parts) if context_parts else "No specific product context available."
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context_text}\n\nCustomer question: {user_query}"}
            ],
            max_tokens=150,
            temperature=0.7,
            stream=True
        )
        
        accumulated_text = ""
        sentence_buffer = ""
        
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                accumulated_text += content
                sentence_buffer += content
                
                # Yield complete sentences for real-time TTS
                if any(punct in content for punct in '.!?'):
                    yield sentence_buffer.strip()
                    sentence_buffer = ""
        
        # Yield any remaining content
        if sentence_buffer.strip():
            yield sentence_buffer.strip()
            
    except Exception as e:
        print(f"GPT Streaming Error: {e}")
        yield "I'm sorry, I'm having trouble processing your request right now. Please try again."

async def process_partial_query(
    partial_query: str,
    product_context: Optional[Dict] = None,
    store_id: Optional[str] = None
) -> str:
    """Process partial query for immediate feedback"""
    
    if len(partial_query.strip()) < 3:
        return ""
    
    # Simple intent detection for immediate responses
    query_lower = partial_query.lower()
    
    if any(word in query_lower for word in ['where', 'location', 'find']):
        if product_context:
            return f"This product is located at {product_context.get('shelf_location', 'unknown location')}."
        return "I can help you find products. What are you looking for?"
    
    if any(word in query_lower for word in ['price', 'cost', 'how much']):
        if product_context:
            return f"This product costs ${product_context.get('price', 'unknown')}."
        return "I can help you with pricing information."
    
    if any(word in query_lower for word in ['stock', 'available', 'inventory']):
        if product_context:
            stock = product_context.get('stock', 0)
            return f"We have {stock} units in stock."
        return "I can check inventory for you."
    
    return ""
