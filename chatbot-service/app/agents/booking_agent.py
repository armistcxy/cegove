# app/agents/booking_agent.py
from app.agents.base import BaseAgent
from app.models.agent_state import AgentState, BookingState, AgentType
from app.services.gemini_service import gemini_service
from app.services.api_client import api_client
from app.services.knowledge_service import knowledge_service
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

# Setup logger
logger = logging.getLogger("BookingAgent")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '\033[94m[%(name)s]\033[0m %(levelname)s: %(message)s'
    ))
    logger.addHandler(handler)
import json
import time
import re

class BookingAgent(BaseAgent):
    """
    Booking Agent - Chuyên về đặt vé
    
    Quy trình đặt vé:
    1. select_movie: Chọn phim
    2. select_cinema: Chọn rạp chiếu
    3. select_showtime: Chọn suất chiếu
    4. view_seats: Hiển thị sơ đồ ghế (pattern image)
    5. select_seats: Chọn ghế cụ thể
    6. confirm: Xác nhận đặt vé
    7. payment: Tạo booking và trả về URL thanh toán
    """
    
    # Đường dẫn đến ảnh pattern ghế
    SEAT_PATTERNS = {
        "pattern1": "pattern1.jpg",
        "pattern2": "pattern2.jpg",
        "pattern3": "pattern3.jpg"
    }
    
    def __init__(self):
        super().__init__("booking")
        
        self.extraction_instruction = """Bạn là trợ lý trích xuất thông tin đặt vé.

QUAN TRỌNG:
- CHỈ trích xuất TÊN PHIM CỤ THỂ (như "Avatar", "The Godfather", "Zootopia")
- KHÔNG lấy từ "phim" đứng một mình làm tên phim
- KHÔNG lấy CÂU HỎI làm tên phim
- Nếu user hỏi "có phim gì", "phim nào", "những phim" → movie_name: null

Ví dụ ĐÚNG:
- "đặt vé Zootopia" → {"movie_name": "Zootopia"}
- "đặt vé phim avatar 2" → {"movie_name": "avatar 2"}
- "book 2 vé Inception" → {"movie_name": "Inception", "num_seats": 2}
- "rạp CGV Times City" → {"cinema_name": "CGV Times City"}
- "suất 7 giờ tối" → {"time_preference": "19:00"}

Ví dụ movie_name phải là null:
- "đặt vé xem phim" → {"movie_name": null}
- "có phim gì đang chiếu" → {"movie_name": null}
- "đặt phim này" → {"movie_name": null, "reference": "this"}

Trả về JSON:
{
    "movie_name": "TÊN PHIM" | null,
    "cinema_name": "TÊN RẠP" | null,
    "num_seats": số ghế | null,
    "seat_codes": ["A1", "A2"] | null,
    "showtime_index": số thứ tự suất | null,
    "time_preference": "giờ" | null,
    "reference": "this" | "that" | null
}"""
        
        self.extraction_model = gemini_service.create_model(self.extraction_instruction)
        
        # Load knowledge path for seat patterns
        self.knowledge_dir = Path(__file__).parent.parent / "knowledges"
    
    async def process(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Xử lý quy trình đặt vé đa bước"""
        
        logger.info(f"{'='*50}")
        logger.info(f"BOOKING AGENT - Processing message: '{message}'")
        logger.info(f"Session: {state.session_id}, User: {state.user_id}")
        
        # Initialize booking state
        if not state.booking_state:
            logger.info("No booking state found, initializing new BookingState")
            state.booking_state = BookingState(step="select_movie")
            
            # *** CHECK FOCUSED MOVIE ***
            # Nếu có focused movie từ việc xem lịch chiếu trước đó, sử dụng nó
            focused = state.get_focused_movie()
            if focused:
                logger.info(f"✅ FOCUSED MOVIE FOUND: {focused.movie_title} (ID: {focused.movie_id})")
                logger.info(f"   Showtimes available: {len(focused.showtimes) if focused.showtimes else 0}")
                state.booking_state.movie_id = focused.movie_id
                state.booking_state.movie_title = focused.movie_title
                state.booking_state.all_showtimes = focused.showtimes
                state.booking_state.step = "select_cinema"  # Skip to cinema selection
                logger.info(f"   → Skipping to step: select_cinema")
            else:
                logger.info("❌ No focused movie in state")
        else:
            logger.info(f"Existing booking state found")
        
        current_step = state.booking_state.step
        logger.info(f"Current step: {current_step}")
        logger.info(f"Booking state: movie={state.booking_state.movie_title}, cinema={state.booking_state.cinema_name}, showtime={state.booking_state.showtime_id}")
        
        # Check for cancel/change intent
        logger.debug(f"Checking for cancel/change intent...")
        change_result = await self._check_change_intent(message, state)
        if change_result:
            logger.info(f"⚠️ Change/cancel intent detected, returning early")
            return change_result
        
        # *** SPECIAL CASE: If step is select_movie but we just set focused movie ***
        # This happens when user says "đặt vé" and we have focused movie
        if current_step == "select_cinema" and state.booking_state.movie_id and not state.booking_state.available_cinemas:
            logger.info(f"🎯 SPECIAL CASE: Focused movie set but no cinemas loaded yet")
            logger.info(f"   → Calling _show_cinemas_with_showtime_hint()")
            # Show cinemas for the focused movie
            return await self._show_cinemas_with_showtime_hint(message, state)
        
        # Process based on step
        handlers = {
            "select_movie": self._handle_select_movie,
            "confirm_movie": self._handle_confirm_movie,
            "select_cinema": self._handle_select_cinema,
            "select_showtime": self._handle_select_showtime,
            "view_seats": self._handle_view_seats,
            "select_seats": self._handle_select_seats,
            "confirm": self._handle_confirm
        }
        
        handler = handlers.get(current_step, self._handle_select_movie)
        logger.info(f"→ Calling handler: {handler.__name__}")
        
        result = await handler(message, state)
        
        logger.info(f"Handler result: step={result.get('metadata', {}).get('step', 'N/A')}")
        logger.debug(f"Response preview: {result.get('response', '')[:100]}...")
        logger.info(f"{'='*50}")
        
        return result
    
    async def can_handle(self, message: str, state: AgentState) -> bool:
        """Check if can handle booking request"""
        keywords = ["đặt vé", "book", "mua vé", "đặt chỗ", "booking"]
        return any(kw in message.lower() for kw in keywords)
    
    async def _check_change_intent(self, message: str, state: AgentState) -> Optional[Dict]:
        """Detect and handle change/cancel intent"""
        message_lower = message.lower()
        
        # Cancel booking
        cancel_keywords = ["hủy", "cancel", "không đặt nữa", "thôi", "bỏ"]
        if any(kw in message_lower for kw in cancel_keywords):
            state.booking_state = None
            state.current_agent = AgentType.ROUTER
            return {
                "response": "✅ Đã hủy đặt vé. Bạn cần gì khác không? 😊",
                "agent": self.name,
                "metadata": {"action": "cancelled"}
            }
        
        # Go back
        back_keywords = ["quay lại", "chọn lại", "đổi phim", "đổi rạp", "đổi suất"]
        if any(kw in message_lower for kw in back_keywords):
            if "phim" in message_lower:
                state.booking_state = BookingState(step="select_movie")
                return {
                    "response": "🔄 Quay lại chọn phim. Bạn muốn xem phim gì?",
                    "agent": self.name,
                    "metadata": {"action": "back_to_movie"}
                }
            elif "rạp" in message_lower:
                state.booking_state.step = "select_cinema"
                return await self._show_cinemas(state)
            elif "suất" in message_lower:
                state.booking_state.step = "select_showtime"
                return await self._show_showtimes(state)
        
        return None
    
    # ==================== STEP 1: SELECT MOVIE ====================
    
    async def _handle_select_movie(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Step 1: Select movie
        
        Handles:
        - Full: "đặt vé Avatar", "mua vé phim Inception"
        - Short: "Avatar", "The Godfather" (user just says movie name)
        - Reference: "phim này", "cái đầu tiên"
        - Index: "số 1", "phim thứ 2" (from shown list)
        """
        
        extraction = await self._extract_info(message)
        movie_name = extraction.get("movie_name")
        
        logger.debug(f"AI extraction result: {extraction}")
        
        # Check for reference words (này, đó) - use context
        if not movie_name:
            reference = extraction.get("reference")
            if reference or self._has_reference_word(message):
                logger.debug(f"Reference word detected, checking context...")
                movie_name = self._get_movie_from_context(state)
                if movie_name:
                    logger.info(f"✅ Got movie from context: {movie_name}")
        
        # Check for index selection ("số 1", "phim thứ 2", "cái đầu")
        if not movie_name:
            movie_name = await self._get_movie_by_index(message, state)
        
        # Fallback: rule-based extraction
        if not movie_name:
            movie_name = self._extract_movie_name_rule(message, state)
        
        # LAST RESORT: If message is short (1-3 words) and not a question,
        # treat it as a movie name directly
        if not movie_name:
            cleaned = message.strip().strip('?!.')
            words = cleaned.split()
            is_question = any(q in message.lower() for q in ["có gì", "phím nào", "những", "các", "danh sách", "?"])
            if 1 <= len(words) <= 5 and not is_question and len(cleaned) >= 2:
                movie_name = cleaned
                logger.info(f"Using raw message as movie name: '{movie_name}'")
        
        logger.info(f"Final movie_name after all extractions: '{movie_name}'")
        
        if not movie_name:
            # *** CHECK FOCUSED MOVIE ***
            # If user says "đặt vé" without movie name, use focused movie if available
            focused = state.get_focused_movie()
            if focused:
                logger.info(f"🎯 No movie name extracted → Using FOCUSED MOVIE: {focused.movie_title}")
                state.booking_state.movie_id = focused.movie_id
                state.booking_state.movie_title = focused.movie_title
                state.booking_state.all_showtimes = focused.showtimes
                state.booking_state.step = "select_cinema"
                
                # Check if user mentioned time or number of seats
                return await self._show_cinemas_with_showtime_hint(message, state)
            
            # Check if user is asking for movie list
            asking_for_list = any(p in message.lower() for p in [
                "có phim gì", "phim nào", "những phim", "các phim", "danh sách", "đang chiếu"
            ])
            
            if asking_for_list:
                movies = await api_client.get_movies(page=1, page_size=5, sort_by="imdb_rating")
                movies_list = movies.get("items", [])
                
                if movies_list:
                    movie_text = "\n".join([
                        f"{i}. **{m.get('series_title')}** ({m.get('released_year', 'N/A')}) - ⭐ {m.get('imdb_rating', 'N/A')}" 
                        for i, m in enumerate(movies_list, 1)
                    ])
                    return {
                        "response": f"""🎬 **Các phim đang có trong hệ thống:**

{movie_text}

💡 Để đặt vé, hãy nói tên phim cụ thể:
- "Đặt vé [tên phim]"
- "Chọn phim số 1" """,
                        "agent": self.name,
                        "metadata": {"step": "select_movie", "showing_suggestions": True}
                    }
            
            return {
                "response": """🎬 Bạn muốn đặt vé xem phim nào?

Cho tôi biết TÊN PHIM bạn muốn xem nhé!
(VD: "Đặt vé Avatar", "Mua vé The Godfather")

Hoặc hỏi "Có phim gì đang chiếu?" để xem danh sách.""",
                "agent": self.name,
                "metadata": {"step": "select_movie"}
            }
        
        # Save num_seats if extracted
        if extraction.get("num_seats"):
            state.booking_state.num_seats = extraction["num_seats"]
        
        # Search movie in DB
        movies = await api_client.search_movies(query=movie_name, limit=3)
        
        if not movies:
            # Try fuzzy search
            fuzzy = await api_client.fuzzy_search_movie(movie_name)
            if fuzzy.get("found"):
                movie = fuzzy["movie"]
                state.booking_state.movie_id = str(movie.get("id"))
                state.booking_state.movie_title = movie.get("series_title")
                state.booking_state.step = "confirm_movie"
                
                return {
                    "response": f"""🔍 Không tìm thấy "{movie_name}" chính xác.

Có phải bạn muốn xem **{fuzzy['matched_title']}**?

Trả lời "có" để tiếp tục.""",
                    "agent": self.name,
                    "metadata": {"step": "confirm_movie", "fuzzy_match": True}
                }
            
            return {
                "response": f"""❌ Phim '{movie_name}' không có trong hệ thống.

Bạn có thể:
🔍 Thử tên phim khác
📋 Hỏi "có phim gì đang chiếu" để xem danh sách""",
                "agent": self.name,
                "metadata": {"step": "select_movie", "movie_not_found": True}
            }
        
        # Found movie
        movie = movies[0]
        state.booking_state.movie_id = str(movie.get("id"))
        state.booking_state.movie_title = movie.get("series_title")
        state.booking_state.step = "select_cinema"
        
        # Move to cinema selection
        return await self._show_cinemas(state)
    
    async def _handle_confirm_movie(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle fuzzy match confirmation"""
        message_lower = message.lower()
        
        if any(w in message_lower for w in ["có", "yes", "ok", "đúng", "phải", "ừ"]):
            state.booking_state.step = "select_cinema"
            return await self._show_cinemas(state)
        
        state.booking_state = BookingState(step="select_movie")
        return {
            "response": "OK, bạn muốn đặt vé phim nào khác?",
            "agent": self.name,
            "metadata": {"step": "select_movie"}
        }
    
    async def _show_cinemas_with_showtime_hint(self, message: str, state: AgentState) -> Dict[str, Any]:
        """
        Handle booking with time hint from focused movie.
        E.g., "đặt vé lúc 11 giờ" → use focused movie + try to match showtime
        """
        logger.info(f"_show_cinemas_with_showtime_hint() called")
        logger.info(f"   Movie: {state.booking_state.movie_title}")
        
        message_lower = message.lower()
        
        # Extract num_seats if mentioned
        extraction = await self._extract_info(message)
        if extraction.get("num_seats"):
            state.booking_state.num_seats = extraction["num_seats"]
            logger.info(f"   Extracted num_seats: {extraction['num_seats']}")
        
        # Try to extract time from message
        time_hint = self._extract_time_hint(message_lower)
        logger.info(f"   Time hint extracted: {time_hint} (hour)")
        
        # Get showtimes from focused movie or fetch new
        showtimes = state.booking_state.all_showtimes
        if not showtimes:
            logger.debug(f"   No cached showtimes, fetching from API...")
            showtimes = await api_client.get_showtimes(movie_id=int(state.booking_state.movie_id))
            state.booking_state.all_showtimes = showtimes
        
        logger.info(f"   Available showtimes: {len(showtimes) if showtimes else 0}")
        
        if not showtimes:
            logger.warning(f"   ❌ No showtimes found!")
            return {
                "response": f"""❌ Phim **{state.booking_state.movie_title}** hiện không có suất chiếu.

Bạn muốn đặt vé phim khác?""",
                "agent": self.name,
                "metadata": {"step": "select_movie", "no_showtimes": True}
            }
        
        # If time hint provided, try to find matching showtime
        matched_showtime = None
        if time_hint:
            matched_showtime = self._find_showtime_by_time(showtimes, time_hint)
            if matched_showtime:
                logger.info(f"   ✅ MATCHED showtime at {time_hint}:00 → ID: {matched_showtime.get('id')}")
            else:
                logger.info(f"   ❌ No showtime found for hour {time_hint}")
        
        if matched_showtime:
            # Found matching showtime, skip to select_seats
            state.booking_state.showtime_id = str(matched_showtime.get("id"))
            state.booking_state.showtime_info = matched_showtime
            state.booking_state.cinema_id = str(matched_showtime.get("cinema_id"))
            
            # Get cinema name
            cinema = knowledge_service.get_cinema_by_id(matched_showtime.get("cinema_id"))
            state.booking_state.cinema_name = cinema.get("name") if cinema else "N/A"
            
            logger.info(f"   → Skipping to view_seats step")
            state.booking_state.step = "view_seats"
            return await self._handle_view_seats(message, state)
        
        # No time hint or no match → show cinemas normally
        logger.info(f"   → No time match, showing cinemas list")
        return await self._show_cinemas(state)
    
    def _extract_time_hint(self, message: str) -> Optional[int]:
        """Extract hour from message like '11 giờ', 'lúc 7h', '19:00'"""
        patterns = [
            r'lúc\s*(\d{1,2})\s*(?:giờ|h|:)',
            r'(\d{1,2})\s*(?:giờ|h)\s*(\d{2})?',
            r'(\d{1,2}):(\d{2})',
            r'suất\s*(\d{1,2})\s*(?:giờ|h)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                hour = int(match.group(1))
                # Adjust for PM if hour is small and context suggests evening
                if hour < 12 and any(w in message for w in ["tối", "chiều"]):
                    hour += 12
                return hour
        
        return None
    
    def _find_showtime_by_time(self, showtimes: List[Dict], target_hour: int) -> Optional[Dict]:
        """Find showtime matching the target hour"""
        for st in showtimes:
            start_time = st.get("start_time", "")
            # Parse hour from ISO format like "2025-12-24T11:00:00"
            hour_match = re.search(r'T(\d{2}):', start_time)
            if hour_match:
                st_hour = int(hour_match.group(1))
                if st_hour == target_hour:
                    return st
        return None
    
    # ==================== STEP 2: SELECT CINEMA ====================
    
    async def _show_cinemas(self, state: AgentState) -> Dict[str, Any]:
        """Show available cinemas for the movie"""
        
        # Get showtimes for this movie to find available cinemas
        showtimes = await api_client.get_showtimes(movie_id=int(state.booking_state.movie_id))
        
        if not showtimes:
            return {
                "response": f"""✅ Phim **{state.booking_state.movie_title}** có trong hệ thống!

❌ Nhưng hiện KHÔNG CÓ suất chiếu nào.

Bạn muốn tìm phim khác?""",
                "agent": self.name,
                "metadata": {"step": "select_movie", "no_showtimes": True}
            }
        
        # Extract unique cinemas from showtimes
        cinema_ids = set()
        cinemas_with_shows = []
        for st in showtimes:
            cinema_id = st.get("cinema_id")
            if cinema_id and cinema_id not in cinema_ids:
                cinema_ids.add(cinema_id)
                # Get cinema info from knowledge
                cinema = knowledge_service.get_cinema_by_id(cinema_id)
                if cinema:
                    num_shows = len([s for s in showtimes if s.get("cinema_id") == cinema_id])
                    cinemas_with_shows.append({
                        "id": cinema_id,
                        "name": cinema.get("name"),
                        "address": cinema.get("address"),
                        "city": cinema.get("city"),
                        "num_shows": num_shows
                    })
        
        # Save available cinemas
        state.booking_state.available_cinemas = cinemas_with_shows
        state.booking_state.all_showtimes = showtimes
        
        if not cinemas_with_shows:
            # Use city grouping from showtimes - show showtimes directly
            cinema_text = "Dữ liệu rạp đang cập nhật. Các suất chiếu có sẵn:\n"
            cinema_text += self._format_showtimes(showtimes[:5])
            state.booking_state.step = "select_showtime"
            state.booking_state.available_showtimes = showtimes[:10]
            return {
                "response": f"""✅ Đặt vé phim **{state.booking_state.movie_title}**

{cinema_text}

💡 Chọn suất chiếu (VD: "suất 1", "suất 19:00")""",
                "agent": self.name,
                "metadata": {"step": "select_showtime", "direct_showtime": True}
            }
        else:
            cinema_text = "\n".join([
                f"{i}. 🏢 **{c['name']}** ({c['city']})\n   📍 {c['address']}\n   🎬 {c['num_shows']} suất chiếu"
                for i, c in enumerate(cinemas_with_shows[:8], 1)
            ])
        
        return {
            "response": f"""✅ Đặt vé phim **{state.booking_state.movie_title}**

🏢 **Chọn rạp chiếu:**

{cinema_text}

💡 Nói tên rạp hoặc số thứ tự (VD: "CGV Times City", "rạp số 1")""",
            "agent": self.name,
            "metadata": {"step": "select_cinema", "cinemas_count": len(cinemas_with_shows)}
        }
    
    async def _handle_select_cinema(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Step 2: Select cinema
        
        Handles:
        - Full: "CGV Times City", "rạp Vincom"
        - Short index: "1", "số 1", "cái đầu", "rạp 2"
        - City: "Hà Nội", "Sài Gòn" (pick first in that city)
        - Partial name: "Times City", "Vincom"
        """
        
        extraction = await self._extract_info(message)
        cinema_name = extraction.get("cinema_name")
        
        available_cinemas = state.booking_state.available_cinemas or []
        message_lower = message.lower().strip()
        
        selected_cinema = None
        
        # 1. Try to match by index ("1", "số 1", "rạp 1", "cái đầu")
        index_patterns = [
            r'^(\d+)$',                          # Just "1", "2"
            r'(?:rạp\s*)?(?:số\s*)?(\d+)',      # "số 1", "rạp số 1"
            r'cái\s*(?:thứ\s*)?(\d+)',           # "cái 1", "cái thứ 2"
        ]
        for pattern in index_patterns:
            match = re.search(pattern, message_lower)
            if match:
                idx = int(match.group(1)) - 1
                if 0 <= idx < len(available_cinemas):
                    selected_cinema = available_cinemas[idx]
                    break
        
        # 2. Ordinal words ("cái đầu", "đầu tiên", "cuối")
        if not selected_cinema:
            ordinal_map = {
                "đầu": 0, "đầu tiên": 0, "thứ nhất": 0, "first": 0,
                "thứ hai": 1, "thứ 2": 1, "second": 1,
                "thứ ba": 2, "thứ 3": 2, "third": 2,
                "cuối": -1, "cuối cùng": -1, "last": -1
            }
            for word, idx in ordinal_map.items():
                if word in message_lower:
                    if idx == -1:
                        idx = len(available_cinemas) - 1
                    if 0 <= idx < len(available_cinemas):
                        selected_cinema = available_cinemas[idx]
                        break
        
        # 3. Try to match by extracted cinema name
        if not selected_cinema and cinema_name:
            for c in available_cinemas:
                if cinema_name.lower() in c.get("name", "").lower():
                    selected_cinema = c
                    break
        
        # 4. Try to match by city name
        if not selected_cinema:
            city_keywords = ["hà nội", "sài gòn", "hồ chí minh", "đà nẵng", "hải phòng", "cần thơ"]
            for city in city_keywords:
                if city in message_lower:
                    for c in available_cinemas:
                        if city in c.get("city", "").lower():
                            selected_cinema = c
                            break
                    break
        
        # 5. Fuzzy match by name parts in message
        if not selected_cinema:
            for c in available_cinemas:
                cinema_words = c.get("name", "").lower().split()
                # Match if any significant word (>3 chars) from cinema name is in message
                if any(word in message_lower for word in cinema_words if len(word) > 3):
                    selected_cinema = c
                    break
        
        # 6. If message is short and looks like a name, search in available
        if not selected_cinema and len(message_lower) > 2:
            for c in available_cinemas:
                if message_lower in c.get("name", "").lower():
                    selected_cinema = c
                    break
        
        if not selected_cinema:
            cinema_text = "\n".join([
                f"{i}. {c['name']} ({c['city']})"
                for i, c in enumerate(available_cinemas[:8], 1)
            ])
            return {
                "response": f"""Tôi chưa hiểu bạn muốn chọn rạp nào. Các rạp có sẵn:

{cinema_text}

Hãy nói rõ hơn (VD: "rạp số 1", "CGV Times City")""",
                "agent": self.name,
                "metadata": {"step": "select_cinema"}
            }
        
        # Save selected cinema
        state.booking_state.cinema_id = str(selected_cinema["id"])
        state.booking_state.cinema_name = selected_cinema["name"]
        state.booking_state.step = "select_showtime"
        
        # Show showtimes for this cinema
        return await self._show_showtimes(state)
    
    # ==================== STEP 3: SELECT SHOWTIME ====================
    
    async def _show_showtimes(self, state: AgentState) -> Dict[str, Any]:
        """Show showtimes for selected cinema"""
        
        all_showtimes = state.booking_state.all_showtimes or []
        cinema_id = state.booking_state.cinema_id
        
        # Filter showtimes by cinema
        if cinema_id:
            showtimes = [st for st in all_showtimes if str(st.get("cinema_id")) == cinema_id]
        else:
            showtimes = all_showtimes[:10]
        
        if not showtimes:
            showtimes = all_showtimes[:10]  # Fallback
        
        state.booking_state.available_showtimes = showtimes
        
        showtimes_text = self._format_showtimes(showtimes[:8])
        
        return {
            "response": f"""🎬 **{state.booking_state.movie_title}**
🏢 Rạp: **{state.booking_state.cinema_name or 'N/A'}**

📅 **Các suất chiếu:**

{showtimes_text}

💡 Chọn suất chiếu (VD: "suất 1", "suất 19:00", "cái đầu tiên")""",
            "agent": self.name,
            "metadata": {"step": "select_showtime", "showtimes_count": len(showtimes)}
        }
    
    async def _handle_select_showtime(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Step 3: Select showtime
        
        Handles:
        - Index: "1", "suất 1", "cái đầu"
        - Time: "7 giờ", "19:00", "7h", "19h30"
        - Period: "tối", "chiều", "sáng", "trưa"
        - Combined: "suất 7 giờ tối"
        """
        
        showtimes = state.booking_state.available_showtimes or []
        
        if not showtimes:
            state.booking_state.step = "select_cinema"
            return await self._show_cinemas(state)
        
        message_lower = message.lower().strip()
        selected_index = None
        
        # 1. Try index patterns ("1", "suất 1", "cái 2")
        index_patterns = [
            r'^(\d+)$',                          # Just "1"
            r'suất\s*(\d+)',                     # "suất 1"
            r'cái\s*(?:thứ\s*)?(\d+)',           # "cái 1"
            r'số\s*(\d+)',                        # "số 1"
        ]
        for pattern in index_patterns:
            match = re.search(pattern, message_lower)
            if match:
                idx = int(match.group(1)) - 1
                if 0 <= idx < len(showtimes):
                    selected_index = idx
                    break
        
        # 2. Ordinal words
        if selected_index is None:
            ordinal_map = {
                "đầu": 0, "đầu tiên": 0, "thứ nhất": 0,
                "thứ hai": 1, "hai": 1,
                "thứ ba": 2, "ba": 2,
                "cuối": -1, "cuối cùng": -1
            }
            for word, idx in ordinal_map.items():
                if word in message_lower:
                    if idx == -1:
                        idx = len(showtimes) - 1
                    if 0 <= idx < len(showtimes):
                        selected_index = idx
                        break
        
        # 3. Match by time ("7 giờ", "19:00", "7h30", "19h")
        if selected_index is None:
            time_patterns = [
                r'(\d{1,2})\s*[:\.h]\s*(\d{2})?',   # 7:30, 19.00, 7h30
                r'(\d{1,2})\s*giờ\s*(\d{2})?',      # 7 giờ, 7 giờ 30
            ]
            for pattern in time_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    hour = int(match.group(1))
                    # Convert to 24h if needed based on context
                    if hour < 12 and any(w in message_lower for w in ["tối", "chiều", "pm"]):
                        hour += 12
                    
                    # Find showtime matching this hour
                    for i, st in enumerate(showtimes):
                        st_time = st.get("start_time", "")
                        if f"{hour:02d}:" in st_time or f"T{hour:02d}:" in st_time:
                            selected_index = i
                            break
                    if selected_index is not None:
                        break
        
        # 4. Match by period ("tối", "chiều", "sáng")
        if selected_index is None:
            period_ranges = {
                "sáng": (6, 12),
                "trưa": (11, 14),
                "chiều": (13, 18),
                "tối": (18, 24),
            }
            for period, (start_h, end_h) in period_ranges.items():
                if period in message_lower:
                    # Find first showtime in this period
                    for i, st in enumerate(showtimes):
                        st_time = st.get("start_time", "")
                        hour_match = re.search(r'T?(\d{2}):', st_time)
                        if hour_match:
                            st_hour = int(hour_match.group(1))
                            if start_h <= st_hour < end_h:
                                selected_index = i
                                break
                    break
        
        # 5. Fallback to original matching
        if selected_index is None:
            selected_index = self._match_showtime_choice(message, showtimes)
        
        if selected_index is None:
            showtimes_text = self._format_showtimes(showtimes[:5])
            return {
                "response": f"""Tôi chưa hiểu bạn muốn chọn suất nào. Các suất có sẵn:

{showtimes_text}

Hãy nói rõ hơn (VD: "suất 1", "suất 19:00")""",
                "agent": self.name,
                "metadata": {"step": "select_showtime"}
            }
        
        selected = showtimes[selected_index]
        state.booking_state.showtime_id = str(selected.get("id"))
        state.booking_state.showtime_info = selected
        state.booking_state.step = "view_seats"
        
        # Move to view seats (show pattern)
        return await self._handle_view_seats(message, state)
    
    # ==================== STEP 4: VIEW SEATS (PATTERN) ====================
    
    async def _handle_view_seats(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Step 4: Show seat pattern image"""
        
        # Get seat availability
        seat_info = await api_client.get_available_seats_count(state.booking_state.showtime_id)
        total_available = seat_info.get("total_available", 0)
        by_type = seat_info.get("by_type", {})
        
        if total_available == 0:
            return {
                "response": f"""❌ Suất chiếu này đã **HẾT GHẾ**!

Bạn muốn:
🔄 Chọn suất khác? Nói "chọn suất khác"
🎬 Chọn phim khác? Nói "đổi phim" """,
                "agent": self.name,
                "metadata": {"step": "select_showtime", "sold_out": True}
            }
        
        # Get seats data for pattern detection
        seats = await api_client.get_showtime_seats_v2(state.booking_state.showtime_id)
        pattern = self._detect_seat_pattern(seats)
        
        # Format seat types
        type_text = self._format_seat_types(by_type)
        
        # Get pattern image path
        pattern_image = self.SEAT_PATTERNS.get(pattern, "pattern1.jpg")
        image_path = str(self.knowledge_dir / pattern_image)
        
        state.booking_state.step = "select_seats"
        state.booking_state.seat_pattern = pattern
        
        return {
            "response": f"""✅ **Đã chọn suất chiếu:**

🎬 **{state.booking_state.movie_title}**
📅 {self._format_time(state.booking_state.showtime_info.get('start_time'))}
🏢 {state.booking_state.cinema_name or 'Rạp chiếu'}

🪑 **Sơ đồ ghế:** (Còn **{total_available}** ghế trống)
{type_text}

📷 Xem sơ đồ ghế bên dưới và chọn ghế bạn muốn:
- Nói mã ghế (VD: "A1, A2", "B5 B6 B7")
- Hoặc nói số lượng (VD: "2 ghế VIP", "3 ghế thường")

⚠️ Ghế màu xám = đã bán, ghế màu = còn trống""",
            "agent": self.name,
            "metadata": {
                "step": "select_seats",
                "available_seats": total_available,
                "seat_pattern": pattern,
                "image_path": image_path
            }
        }
    
    def _detect_seat_pattern(self, seats: List[Dict]) -> str:
        """Detect which seat pattern to show based on seat data"""
        if not seats:
            return "pattern1"
        
        # Count rows and columns
        rows = set()
        max_col = 0
        for seat in seats:
            pos = seat.get("position", {})
            row = pos.get("row", "")
            col = pos.get("number", 0)
            if row:
                rows.add(row)
            if col > max_col:
                max_col = col
        
        num_rows = len(rows)
        
        # Simple heuristic for pattern selection
        if num_rows <= 6:
            return "pattern1"  # Small room
        elif num_rows <= 10:
            return "pattern2"  # Medium room
        else:
            return "pattern3"  # Large room
    
    # ==================== STEP 5: SELECT SEATS ====================
    
    async def _handle_select_seats(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Step 5: Select specific seats"""
        
        message_lower = message.lower().strip()
        extraction = await self._extract_info(message)
        
        # Get available seats
        seats = await api_client.get_showtime_seats_v2(state.booking_state.showtime_id)
        available = [s for s in seats if s.get("status_text", "").lower() == "available"]
        
        # 1. Try to extract seat codes first (e.g., "A1 A2", "B5, B6")
        seat_codes = extraction.get("seat_codes") or self._extract_seat_codes(message)
        
        # 2. Try to parse number of seats from short messages
        num_seats = extraction.get("num_seats") or state.booking_state.num_seats
        
        # Parse number from short messages like "2", "3 ghế", "2 vé", "hai ghế"
        if not num_seats:
            num_match = re.search(r'^(\d+)\s*(ghế|vé|cái)?$', message_lower)
            if num_match:
                num_seats = int(num_match.group(1))
            else:
                # Vietnamese number words
                vn_numbers = {
                    "một": 1, "hai": 2, "ba": 3, "bốn": 4, "năm": 5,
                    "sáu": 6, "bảy": 7, "tám": 8, "chín": 9, "mười": 10
                }
                for word, num in vn_numbers.items():
                    if word in message_lower:
                        num_seats = num
                        break
        
        num_seats = max(1, min(num_seats or 1, 10))
        state.booking_state.num_seats = num_seats
        
        # Check availability
        if len(available) < num_seats:
            return {
                "response": f"""❌ Chỉ còn **{len(available)}** ghế trống, không đủ {num_seats} ghế.

Bạn muốn:
1️⃣ Giảm số vé
2️⃣ Chọn suất khác (nói "đổi suất")""",
                "agent": self.name,
                "metadata": {"step": "select_seats", "insufficient_seats": True}
            }
        
        selected = []
        if seat_codes:
            for code in seat_codes:
                for seat in available:
                    if seat.get("label", "").upper() == code.upper():
                        selected.append(seat)
                        break
            
            if len(selected) < len(seat_codes):
                available_labels = ', '.join([s.get('label') for s in available[:20]])
                return {
                    "response": f"""❌ Một số ghế bạn chọn không khả dụng.

Ghế còn trống: {available_labels}

Hãy chọn lại hoặc nói số lượng (VD: "3 ghế")""",
                    "agent": self.name,
                    "metadata": {"step": "select_seats"}
                }
        
        # 3. If no seat codes but have number, or just a number message, auto-select
        if not selected and num_seats > 0:
            selected = self._auto_select_seats(available, num_seats)
        
        if not selected:
            return {
                "response": """Vui lòng cho tôi biết bạn muốn chọn ghế nào:
- Mã ghế cụ thể (VD: "A1 A2", "B5, B6")
- Hoặc số lượng (VD: "2 ghế", "3 ghế VIP")""",
                "agent": self.name,
                "metadata": {"step": "select_seats"}
            }
        
        total_price = sum(s.get("pricing", {}).get("amount", 0) for s in selected)
        
        state.booking_state.seat_ids = [s.get("id") for s in selected]
        state.booking_state.seat_names = [s.get("label") for s in selected]
        state.booking_state.total_price = total_price
        state.booking_state.step = "confirm"
        
        return {
            "response": f"""✅ **Đã chọn ghế thành công!**

📋 **THÔNG TIN ĐẶT VÉ**
━━━━━━━━━━━━━━━━━━━━━
🎬 Phim: **{state.booking_state.movie_title}**
📅 Suất: {self._format_time(state.booking_state.showtime_info.get('start_time'))}
🏢 Rạp: {state.booking_state.cinema_name or 'N/A'}
🪑 Ghế: **{', '.join(state.booking_state.seat_names)}**
💰 Tổng tiền: **{total_price:,.0f} VNĐ**
━━━━━━━━━━━━━━━━━━━━━

✅ **Xác nhận đặt vé?** (Có/Không)""",
            "agent": self.name,
            "metadata": {"step": "confirm", "total_price": total_price}
        }
    
    def _auto_select_seats(self, available: List[Dict], num_seats: int) -> List[Dict]:
        """Auto-select best adjacent seats"""
        if not available or num_seats <= 0:
            return []
        
        # Sort by row and number
        sorted_seats = sorted(available, key=lambda s: (
            s.get("position", {}).get("row", "Z"),
            s.get("position", {}).get("number", 0)
        ))
        
        # Try to find adjacent seats
        for i in range(len(sorted_seats) - num_seats + 1):
            candidate = sorted_seats[i:i + num_seats]
            # Check if same row
            rows = set(s.get("position", {}).get("row") for s in candidate)
            if len(rows) == 1:
                return candidate
        
        # Fallback: just take first available
        return sorted_seats[:num_seats]
    
    def _extract_seat_codes(self, message: str) -> List[str]:
        """Extract seat codes from message (A1, B2, etc.)"""
        return re.findall(r'\b([A-K]\d{1,2})\b', message.upper())
    
    # ==================== STEP 6: CONFIRM ====================
    
    async def _handle_confirm(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Step 6: Confirm and create booking"""
        
        message_lower = message.lower().strip()
        
        # Positive confirmation words
        confirm_words = [
            "có", "yes", "ok", "okay", "đồng ý", "xác nhận", "confirm",
            "được", "oke", "ừ", "uh", "yep", "đặt", "đặt luôn", "chắc chắn",
            "đúng rồi", "đúng", "tiếp tục", "thanh toán"
        ]
        
        # Negative words
        cancel_words = [
            "không", "no", "hủy", "cancel", "thôi", "đổi", "bỏ",
            "không đặt", "hủy bỏ"
        ]
        
        is_confirm = any(w == message_lower or w in message_lower for w in confirm_words)
        is_cancel = any(w == message_lower or w in message_lower for w in cancel_words)
        
        if is_cancel and not is_confirm:
            # User wants to cancel
            return {
                "response": """❌ Đã hủy đặt vé.

Bạn muốn:
🔄 Chọn ghế khác? Nói "chọn ghế lại"
🎬 Đặt vé phim khác? Nói "đặt vé phim" """,
                "agent": self.name,
                "metadata": {"step": "cancelled"}
            }
        
        if is_confirm:
            # Create booking
            booking = await api_client.create_booking(
                user_id=state.user_id,
                showtime_id=state.booking_state.showtime_id,
                seat_ids=state.booking_state.seat_ids
            )
            
            if not booking:
                return {
                    "response": """❌ Có lỗi khi tạo booking. Ghế có thể đã được người khác đặt.

Bạn muốn:
🔄 Thử lại? Nói "chọn ghế lại"
🎬 Đặt vé khác? Nói "đặt vé phim khác" """,
                    "agent": self.name,
                    "metadata": {"step": "select_seats", "booking_failed": True}
                }
            
            booking_id = booking.get("id", "N/A")
            total_price = state.booking_state.total_price or booking.get("total_price", 0)
            
            # Create payment
            payment = await api_client.create_payment(
                booking_id=booking_id,
                amount=total_price,
                user_id=state.user_id
            )
            
            payment_url = payment.get("payment_url") if payment else None
            payment_info = ""
            if payment_url:
                payment_info = f"\n\n🔗 **Link thanh toán:** {payment_url}"
            elif payment:
                payment_info = f"\n\n💳 **Mã thanh toán:** {payment.get('transaction_id', booking_id)}"
            
            response = f"""🎉 **ĐẶT VÉ THÀNH CÔNG!**

📋 **Mã booking:** `{booking_id}`
🎬 Phim: {state.booking_state.movie_title}
📅 Suất: {self._format_time(state.booking_state.showtime_info.get('start_time'))}
🏢 Rạp: {state.booking_state.cinema_name or 'N/A'}
🪑 Ghế: {', '.join(state.booking_state.seat_names)}
💰 Tổng tiền: **{total_price:,.0f} VNĐ**
{payment_info}

⏰ Vui lòng thanh toán trong **15 phút**.

Cảm ơn bạn đã sử dụng dịch vụ! 🙏"""
            
            # Reset booking state
            state.booking_state = None
            state.current_agent = AgentType.ROUTER
            
            return {
                "response": response,
                "agent": self.name,
                "metadata": {
                    "step": "completed",
                    "booking_id": booking_id,
                    "payment": payment
                }
            }
        
        # Not clear, ask again
        return {
            "response": f"""📋 **XÁC NHẬN ĐẶT VÉ**

🎬 Phim: **{state.booking_state.movie_title}**
📅 Suất: {self._format_time(state.booking_state.showtime_info.get('start_time'))}
🏢 Rạp: {state.booking_state.cinema_name or 'N/A'}
🪑 Ghế: **{', '.join(state.booking_state.seat_names)}**
💰 Tổng tiền: **{state.booking_state.total_price:,.0f} VNĐ**

✅ Xác nhận đặt vé? (Có/Không)""",
            "agent": self.name,
            "metadata": {"step": "confirm"}
        }
    
    # ==================== HELPER METHODS ====================
    
    async def _extract_info(self, message: str) -> Dict[str, Any]:
        """Extract booking info using AI"""
        try:
            prompt = f"""Trích xuất thông tin từ: "{message}"

Trả về JSON với các trường:
- movie_name: tên phim (nếu có)
- cinema_name: tên rạp (nếu có)
- num_seats: số ghế (nếu có)
- seat_codes: mã ghế như ["A1", "A2"] (nếu có)
- showtime_index: số thứ tự suất (nếu có)
- reference: "this"/"that" nếu dùng "này"/"đó"
"""
            
            response = self.extraction_model.generate_content(prompt)
            text = response.text.strip()
            
            if text.startswith("```"):
                text = re.sub(r'^```\w*\n?', '', text)
                text = re.sub(r'\n?```$', '', text)
            
            return json.loads(text.strip())
        except Exception as e:
            print(f"[BookingAgent] AI extraction failed: {e}")
            return self._simple_extract(message)
    
    def _simple_extract(self, message: str) -> Dict[str, Any]:
        """Simple rule-based extraction"""
        result = {}
        message_lower = message.lower()
        
        # Extract number of seats
        match = re.search(r'(\d+)\s*(vé|ghế|chỗ|seats?)', message_lower)
        if match:
            result["num_seats"] = int(match.group(1))
        
        # Extract seat codes
        codes = self._extract_seat_codes(message)
        if codes:
            result["seat_codes"] = codes
        
        # Check for reference words
        if any(w in message_lower for w in ["này", "đó", "kia"]):
            result["reference"] = "this"
        
        return result
    
    def _extract_movie_name_rule(self, message: str, state: AgentState) -> Optional[str]:
        """Rule-based movie name extraction"""
        message_lower = message.lower()
        
        # Skip if asking question
        question_patterns = [r"có phim", r"phim (gì|nào)", r"những phim", r"các phim", r"danh sách"]
        if any(re.search(p, message_lower) for p in question_patterns):
            return None
        
        # Check reference words
        if self._has_reference_word(message):
            return self._get_movie_from_context(state)
        
        # Remove booking keywords
        patterns = [
            r'đặt\s*vé\s*(phim\s*)?', r'mua\s*vé\s*(phim\s*)?',
            r'book\s*(vé\s*)?(phim\s*)?', r'muốn\s*xem\s*(phim\s*)?'
        ]
        
        movie_name = message
        for p in patterns:
            movie_name = re.sub(p, '', movie_name, flags=re.IGNORECASE)
        
        # Remove noise words
        noise = ['này', 'đó', 'tôi', 'cho', 'gì', 'nào', 'có', 'đang', 'chiếu']
        for w in noise:
            movie_name = re.sub(rf'\b{w}\b', '', movie_name, flags=re.IGNORECASE)
        
        movie_name = movie_name.strip().strip('?!.,')
        
        if not movie_name or movie_name.lower() in ['phim', 'vé', '']:
            return self._get_movie_from_context(state)
        
        return movie_name if len(movie_name) > 1 else None
    
    def _has_reference_word(self, message: str) -> bool:
        """Check for reference words"""
        return any(w in message.lower() for w in ["này", "đó", "kia", "trên", "vừa", "nãy"])
    
    async def _get_movie_by_index(self, message: str, state: AgentState) -> Optional[str]:
        """Get movie by index when user says "số 1", "phim 2", "cái đầu"
        
        Works with movie list shown in previous assistant message.
        """
        message_lower = message.lower().strip()
        
        # Parse index from message
        index = None
        
        # Pattern 1: "số 1", "phim số 2", "cái số 3"
        match = re.search(r'(?:số|phim|cái)\s*(\d+)', message_lower)
        if match:
            index = int(match.group(1)) - 1
        
        # Pattern 2: Just a number "1", "2", "3"
        if index is None and message_lower.isdigit():
            index = int(message_lower) - 1
        
        # Pattern 3: Ordinal words
        if index is None:
            ordinal_map = {
                "đầu tiên": 0, "đầu": 0, "thứ nhất": 0, "cái đầu": 0, "first": 0,
                "thứ hai": 1, "thứ 2": 1, "second": 1,
                "thứ ba": 2, "thứ 3": 2, "third": 2,
                "thứ tư": 3, "thứ 4": 3,
                "thứ năm": 4, "thứ 5": 4,
                "cuối": -1, "cuối cùng": -1, "last": -1
            }
            for word, idx in ordinal_map.items():
                if word in message_lower:
                    index = idx
                    break
        
        if index is None:
            return None
        
        # Get movie list from previous message
        movie_titles = []
        for msg in reversed(state.history[-5:]):
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                # Find numbered movie list (1. **Movie Title** or 1️⃣ **Movie Title**)
                matches = re.findall(r'(?:\d+[.️⃣]\s*\*\*([^*]+)\*\*|\d+[.️⃣]\s+([^\(]+)\s*\()', content)
                if matches:
                    for m in matches:
                        title = m[0] or m[1]
                        if title:
                            movie_titles.append(title.strip())
                    break
        
        if not movie_titles:
            return None
        
        # Handle negative index (cuối cùng)
        if index == -1:
            index = len(movie_titles) - 1
        
        if 0 <= index < len(movie_titles):
            return movie_titles[index]
        
        return None
    
    def _get_movie_from_context(self, state: AgentState) -> Optional[str]:
        """Get movie from conversation context"""
        if state.movie_context and state.movie_context.movie_titles:
            return state.movie_context.movie_titles[0]
        
        for msg in reversed(state.history[-5:]):
            if msg.get("role") == "assistant":
                match = re.search(r'\*\*([^*]+)\*\*\s*\(\d{4}\)', msg.get("content", ""))
                if match:
                    return match.group(1)
        return None
    
    def _format_showtimes(self, showtimes: List[Dict]) -> str:
        """Format showtimes list"""
        lines = []
        for i, st in enumerate(showtimes, 1):
            time_str = self._format_time(st.get('start_time'))
            price = st.get('base_price', 0)
            cinema = st.get('cinema_name', '')
            lines.append(f"{i}️⃣ {time_str} | 💰 {price:,.0f}đ" + (f" | 🏢 {cinema}" if cinema else ""))
        return "\n".join(lines)
    
    def _format_time(self, time_str: str) -> str:
        """Format ISO time string"""
        if not time_str:
            return "N/A"
        if "T" in str(time_str):
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                return dt.strftime("%H:%M %d/%m/%Y")
            except:
                pass
        return str(time_str)
    
    def _format_seat_types(self, by_type: Dict[str, int]) -> str:
        """Format seat types"""
        if not by_type:
            return ""
        type_names = {"STANDARD": "🟢 Thường", "VIP": "🟡 VIP", "COUPLE": "💜 Đôi"}
        return "\n".join([f"  {type_names.get(t, t)}: {c} ghế" for t, c in by_type.items()])
    
    def _match_showtime_choice(self, message: str, showtimes: List[Dict]) -> Optional[int]:
        """Match user's showtime choice"""
        message_lower = message.lower()
        
        ordinals = {
            "1": 0, "2": 1, "3": 2, "4": 3, "5": 4,
            "đầu": 0, "thứ nhất": 0, "suất 1": 0,
            "thứ hai": 1, "suất 2": 1,
            "thứ ba": 2, "suất 3": 2,
        }
        
        for key, idx in ordinals.items():
            if key in message_lower and idx < len(showtimes):
                return idx
        
        # Match by time
        time_match = re.search(r'(\d{1,2})[:\.]?(\d{2})?', message)
        if time_match:
            hour = int(time_match.group(1))
            for i, st in enumerate(showtimes):
                if str(hour) in st.get("start_time", ""):
                    return i
        
        return None
