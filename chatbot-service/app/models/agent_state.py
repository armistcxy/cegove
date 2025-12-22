from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class AgentType(str, Enum):
    ROUTER = "router"
    MOVIE = "movie"
    BOOKING = "booking"

class BookingState(BaseModel):
    """Trạng thái của booking flow"""
    step: str  # "select_movie", "select_showtime", "select_seats", "confirm"
    movie_id: Optional[str] = None
    movie_title: Optional[str] = None
    showtime_id: Optional[str] = None
    showtime_info: Optional[Dict] = None
    seat_ids: Optional[List[str]] = None
    total_price: Optional[float] = None

class AgentState(BaseModel):
    """Trạng thái chung của conversation"""
    session_id: str
    user_id: str
    current_agent: AgentType
    booking_state: Optional[BookingState] = None
    context: Dict[str, Any] = {}
    history: List[Dict] = []