from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from models.schemas import VoiceResponse, User
from routers.auth import get_current_user
from services.openai_stt import transcribe_audio
from services.gpt_agent import process_query
from services.sesame_tts import generate_speech
from services.product_query import get_product_context
import base64

router = APIRouter()

@router.post("/query", response_model=VoiceResponse)
async def voice_query(
    audio: UploadFile = File(...),
    user_id: str = Form(...),
    product_id: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    try:
        # Validate audio file
        if not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Invalid audio file")
        
        # Read audio data
        audio_data = await audio.read()
        
        # Step 1: STT - Transcribe audio using Sesame CSM
        transcription = await transcribe_audio(audio_data)
        
        # Step 2: Get product context if product_id provided
        product_context = None
        if product_id:
            product_context = await get_product_context(product_id)
        
        # Step 3: LLM - Process query with GPT
        response_text = await process_query(
            transcription, 
            product_context, 
            current_user.current_store_id
        )
        
        # Step 4: TTS - Generate speech from response
        audio_bytes = await generate_speech(response_text)
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return VoiceResponse(
            text=response_text,
            audio=audio_base64
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing voice query: {str(e)}"
        )
