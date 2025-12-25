from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    """Message từ user"""
    message: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    """Response trả về user"""
    session_id: str
    message: str
    agent: str  # Agent nào đã xử lý
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class ConversationHistory(BaseModel):
    """Lịch sử hội thoại"""
    role: str  # "user" hoặc "assistant"
    content: str
    timestamp: datetime
    agent: Optional[str] = None