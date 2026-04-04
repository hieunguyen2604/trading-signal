from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from services.ai_service import ai_service

router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    try:
        # Convert Pydantic models to flat dictionaries for ai_service
        messages_dict = [{"role": m.role, "content": m.content} for m in request.messages]
        response_text = await ai_service.chat(messages_dict)
        return ChatResponse(response=response_text)
    except Exception as e:
        print(f"API AI Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
