from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class AgentType(str, Enum):
    ROUTER = "router"
    MOVIE = "movie"
    BOOKING = "booking"
    CONTEXT = "context"

class BookingState(BaseModel):
    """
    Trạng thái của booking flow - Hỗ trợ Scenario 4, 6, 8
    """
    step: str  # "select_movie", "select_showtime", "select_seats", "confirm", "payment"
    movie_id: Optional[str] = None
    movie_title: Optional[str] = None
    cinema_id: Optional[str] = None
    cinema_name: Optional[str] = None
    showtime_id: Optional[str] = None
    showtime_info: Optional[Dict] = None
    seat_ids: Optional[List[str]] = None
    seat_names: Optional[List[str]] = None
    num_seats: Optional[int] = None
    total_price: Optional[float] = None
    # Lưu danh sách để user có thể chọn
    available_showtimes: Optional[List[Dict]] = None
    available_seats: Optional[List[Dict]] = None

class MovieContext(BaseModel):
    """Lưu context về phim đã đề cập - Hỗ trợ Scenario 5"""
    movie_ids: List[str] = []
    movie_titles: List[str] = []
    last_search_params: Optional[Dict] = None

class AgentState(BaseModel):
    """Trạng thái chung của conversation"""
    session_id: str
    user_id: str
    current_agent: AgentType
    booking_state: Optional[BookingState] = None
    movie_context: Optional[MovieContext] = None  # THÊM: Context phim
    context: Dict[str, Any] = {}
    history: List[Dict] = []
    
    def get_movie_by_index(self, index: int) -> Optional[Dict]:
        """Lấy phim theo thứ tự trong context - Scenario 5"""
        if self.movie_context and 0 <= index < len(self.movie_context.movie_ids):
            return {
                "id": self.movie_context.movie_ids[index],
                "title": self.movie_context.movie_titles[index]
            }
        return None
    
    def update_movie_context(self, movies: List[Dict]):
        """Cập nhật context phim - Scenario 5"""
        if not self.movie_context:
            self.movie_context = MovieContext()
        self.movie_context.movie_ids = [m.get("id") for m in movies[:10]]
        self.movie_context.movie_titles = [m.get("series_title") for m in movies[:10]]
    
    def reset_booking(self):
        """Reset booking state - Scenario 6"""
        self.booking_state = None
        self.current_agent = AgentType.ROUTER