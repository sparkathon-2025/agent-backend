from fastapi import APIRouter, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from models.schemas import VoiceResponse
from services.deepgram_stt import transcribe_audio, create_streaming_deepgram
from services.gpt_agent import process_query, process_query_streaming, process_partial_query
from services.sesame_tts import generate_speech, generate_speech_streaming, add_text_to_stream, complete_stream, list_available_voices
from services.product_query import get_product_context
import base64
import json
import uuid
import asyncio
import logging

router = APIRouter()

@router.post("/query", response_model=VoiceResponse)
async def voice_query(
    audio: UploadFile = File(...),
    product_id: str = Form(None),
    store_id: str = Form(None)
):
    try:
        # Validate audio file
        if not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Invalid audio file")
        
        # Read audio data
        audio_data = await audio.read()
        
        # Step 1: STT - Transcribe audio using Deepgram
        transcription = await transcribe_audio(audio_data)
        
        # Step 2: Get product context if product_id provided
        product_context = None
        if product_id:
            product_context = await get_product_context(product_id)
        
        # Step 3: LLM - Process query with GPT
        response_text = await process_query(
            transcription, 
            product_context, 
            store_id
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

@router.websocket("/stream")
async def voice_stream(websocket: WebSocket):
    """Real-time voice interaction WebSocket endpoint"""
    await websocket.accept()
    
    session_id = str(uuid.uuid4())
    streaming_stt = None
    
    try:
        # Initialize streaming STT
        streaming_stt = await create_streaming_deepgram()
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            if message_type == "start_session":
                # Session started
                await websocket.send_text(json.dumps({
                    "type": "session_started",
                    "session_id": session_id
                }))
            
            elif message_type == "audio_chunk":
                # Process audio chunk
                audio_data = base64.b64decode(message["audio"])
                
                # Send to Deepgram
                await streaming_stt.send_audio(audio_data)
                
                # Get latest transcription
                transcription, is_final = streaming_stt.get_latest_transcription()
                
                if transcription:
                    # Send transcription to client
                    await websocket.send_text(json.dumps({
                        "type": "transcript",
                        "text": transcription,
                        "is_final": is_final
                    }))
                    
                    # Process final transcription
                    if is_final:
                        await _process_final_query(
                            websocket, 
                            session_id, 
                            transcription,
                            message.get("product_context"),
                            message.get("store_id")
                        )
            
            elif message_type == "end_audio":
                # Finalize transcription and process
                final_transcription = await streaming_stt.finish_and_get_final()
                
                if final_transcription:
                    await _process_final_query(
                        websocket,
                        session_id,
                        final_transcription,
                        message.get("product_context"),
                        message.get("store_id")
                    )
            
            elif message_type == "get_voices":
                # Send available voices
                voices = await list_available_voices()
                await websocket.send_text(json.dumps({
                    "type": "voices",
                    "voices": voices
                }))
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": str(e)
        }))
    finally:
        # Cleanup
        if streaming_stt:
            await streaming_stt.close_connection()
        complete_stream(session_id)

async def _process_final_query(
    websocket: WebSocket,
    session_id: str,
    transcription: str,
    product_context: dict = None,
    store_id: str = None
):
    """Process final query and stream response"""
    
    try:
        # Send final transcription
        await websocket.send_text(json.dumps({
            "type": "final_transcript", 
            "text": transcription
        }))
        
        # Start streaming TTS
        tts_task = asyncio.create_task(
            _stream_tts_audio(websocket, session_id)
        )
        
        # Process query with streaming LLM
        full_response = ""
        async for response_chunk in process_query_streaming(
            transcription, 
            product_context, 
            store_id
        ):
            full_response += response_chunk + " "
            
            # Send text chunk to client
            await websocket.send_text(json.dumps({
                "type": "response_chunk",
                "text": response_chunk
            }))
            
            # Add to TTS stream
            add_text_to_stream(session_id, response_chunk)
        
        # Complete TTS stream
        complete_stream(session_id)
        
        # Wait for TTS to finish
        await tts_task
        
        # Send completion signal
        await websocket.send_text(json.dumps({
            "type": "response_complete",
            "full_text": full_response.strip()
        }))
        
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Processing error: {str(e)}"
        }))

async def _stream_tts_audio(websocket: WebSocket, session_id: str):
    """Stream TTS audio to client"""
    
    try:
        async for audio_chunk in generate_speech_streaming(session_id):
            if audio_chunk:
                audio_b64 = base64.b64encode(audio_chunk).decode('utf-8')
                await websocket.send_text(json.dumps({
                    "type": "audio_chunk",
                    "audio": audio_b64
                }))
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error", 
            "message": f"TTS streaming error: {str(e)}"
        }))
