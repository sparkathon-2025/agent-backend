import openai
import os
from typing import Optional, Dict

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
            model="gpt-4",
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
