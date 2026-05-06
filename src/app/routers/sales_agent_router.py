from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
import os

# Importar servicios creados arriba
from app.services.sales_agent import SalesAgent
from app.services.voice_pipeline_service import VoicePipelineService

router = APIRouter(prefix="/sales", tags=["Sales Agent"])

class ChatRequest(BaseModel):
    message: str
    session_id: str
    is_premium: bool = False

@router.post("/chat")
async def chat_with_agent(request: ChatRequest):
    """Endpoint principal para chat de texto con el agente de ventas"""
    try:
        agent = SalesAgent(session_id=request.session_id, is_premium=request.is_premium)
        response = await agent.chat(request.message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/voice/stream")
async def voice_stream_endpoint(websocket: WebSocket, tenant_id: Optional[str] = None, token: Optional[str] = None):
    """Endpoint WebSocket para voz en tiempo real (Pipecat)"""
    await websocket.accept()
    
    # Default config: Open Source pipeline (Standard Tier)
    tenant_config = {
        "is_premium": False,  # Por defecto, usar pipeline open-source
        "locale": "es",       # Detectar desde Accept-Language o perfil de usuario
        "ollama_url": "http://localhost:11434/v1",
    }
    
    try:
        service = VoicePipelineService(tenant_config)
        await service.process_audio_stream(websocket)
    except Exception as e:
        try:
            await websocket.send_json({"error": f"Error en pipeline de voz: {str(e)}"})
            await websocket.close()
        except:
            pass
