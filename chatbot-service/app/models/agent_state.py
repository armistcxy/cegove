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
    
    Quy trình: select_movie → select_cinema → select_showtime → view_seats → select_seats → confirm
    """
    step: str  # "select_movie", "select_cinema", "select_showtime", "view_seats", "select_seats", "confirm"
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
    seat_pattern: Optional[str] = None  # pattern1, pattern2, pattern3
    # Lưu danh sách để user có thể chọn
    available_showtimes: Optional[List[Dict]] = None
    available_cinemas: Optional[List[Dict]] = None
    all_showtimes: Optional[List[Dict]] = None  # All showtimes for movie (before filtering by cinema)
    available_seats: Optional[List[Dict]] = None

class MovieContext(BaseModel):
    """Lưu context về phim đã đề cập - Hỗ trợ Scenario 5"""
    movie_ids: List[str] = []
    movie_titles: List[str] = []
    last_search_params: Optional[Dict] = None

class FocusedMovie(BaseModel):
    """
    Phim đang được focus trong conversation.
    Khi user xem lịch chiếu phim X, phim X trở thành focused movie.
    Khi user nói "đặt vé" mà không chỉ định phim → dùng focused movie.
    """
    movie_id: str
    movie_title: str
    showtimes: Optional[List[Dict]] = None  # Lịch chiếu đã load

class AgentState(BaseModel):
    """Trạng thái chung của conversation"""
    session_id: str
    user_id: str
    current_agent: AgentType
    booking_state: Optional[BookingState] = None
    movie_context: Optional[MovieContext] = None  # Context phim đã đề cập
    focused_movie: Optional[FocusedMovie] = None  # Phim đang được focus (vừa xem lịch chiếu)
    context: Dict[str, Any] = {}
    history: List[Dict] = []
    
    def set_focused_movie(self, movie_id: str, movie_title: str, showtimes: List[Dict] = None):
        """Set phim đang được focus"""
        self.focused_movie = FocusedMovie(
            movie_id=movie_id,
            movie_title=movie_title,
            showtimes=showtimes
        )
    
    def get_focused_movie(self) -> Optional[FocusedMovie]:
        """Lấy phim đang focus"""
        return self.focused_movie
    
    def clear_focused_movie(self):
        """Xóa focused movie"""
        self.focused_movie = None
    
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