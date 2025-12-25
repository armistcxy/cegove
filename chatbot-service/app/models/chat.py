# app/models/chat.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class QuickReplyChip(BaseModel):
    """A clickable chip/button in the chat response."""
    type: Literal["movie", "showtime", "seat", "cinema", "action", "link"]
    label: str
    id: Optional[str] = None  # Entity ID for navigation
    action: Optional[str] = None  # Action to trigger (book, showtimes, etc.)
    url: Optional[str] = None  # External URL for links
    movie_id: Optional[int] = None
    cinema_id: Optional[int] = None


class ChatMetadata(BaseModel):
    """Structured metadata for frontend rendering."""
    intent: Optional[str] = None  # Detected intent
    chips: List[QuickReplyChip] = []  # Quick reply options


class ChatMessage(BaseModel):
    """Message from user."""
    user_id: str
    message: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    chip_data: Optional[Dict[str, Any]] = None  # Data from clicked chip


class ChatResponse(BaseModel):
    """Response to user with structured data."""
    session_id: str
    message: str
    agent: str = "claude"
    timestamp: datetime
    metadata: Optional[ChatMetadata] = None


class ConversationHistory(BaseModel):
    """History entry for conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    agent: Optional[str] = None
