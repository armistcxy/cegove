# app/agents/booking_agent.py
from app.agents.base import BaseAgent
from app.models.agent_state import AgentState, BookingState
from app.services.gemini_service import gemini_service
from app.services.api_client import api_client
from typing import Dict, Any
import json
import time

class BookingAgent(BaseAgent):
    """
    Booking Agent - Chuyên về đặt vé
    """
    
    def __init__(self):
        super().__init__("booking")
        
        # System instruction cho extraction
        self.extraction_instruction = """Bạn là trợ lý trích xuất thông tin đặt vé.

QUAN TRỌNG:
- Chỉ trích xuất thông tin user CUNG CẤP
- KHÔNG tự thêm thông tin không có
- KHÔNG đoán tên phim/rạp nếu user không nói rõ

Trả về JSON chính xác. Nếu thiếu thông tin → trả null."""
        
        # System instruction cho showtime matching
        self.matching_instruction = """Chọn suất chiếu từ DANH SÁCH ĐƯỢC CUNG CẤP.

QUY TẮC:
- CHỈ chọn trong danh sách có sẵn
- KHÔNG tự tạo suất chiếu mới
- Nếu không khớp → chọn gần nhất và giải thích

Trả JSON với showtime_index từ danh sách."""
        
        # Khởi tạo models một lần
        self.extraction_model = gemini_service.create_model(self.extraction_instruction)
        self.matching_model = gemini_service.create_model(self.matching_instruction)
    
    async def process(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Xử lý quy trình đặt vé"""
        
        # Initialize booking state if not exists
        if not state.booking_state:
            state.booking_state = BookingState(step="select_movie")
        
        current_step = state.booking_state.step
        
        # Process based on current step
        if current_step == "select_movie":
            return await self._handle_select_movie(message, state)
        
        elif current_step == "select_showtime":
            return await self._handle_select_showtime(message, state)
        
        elif current_step == "select_seats":
            return await self._handle_select_seats(message, state)
        
        elif current_step == "confirm":
            return await self._handle_confirm(message, state)
        
        else:
            # Reset to start
            state.booking_state.step = "select_movie"
            return await self._handle_select_movie(message, state)
    
    async def can_handle(self, message: str, state: AgentState) -> bool:
        """Check if can handle booking request"""
        keywords = ["đặt vé", "book", "mua vé", "đặt chỗ", "booking"]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in keywords)
    
    async def _extract_with_retry(self, prompt: str) -> Dict[str, Any]:
        """Helper to extract info with retry logic"""
        try:
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    response = self.extraction_model.generate_content(prompt)
                    
                    # Parse JSON
                    text = response.text.strip()
                    if text.startswith("```json"):
                        text = text[7:]
                    if text.startswith("```"):
                        text = text[3:]
                    if text.endswith("```"):
                        text = text[:-3]
                    text = text.strip()
                    
                    return json.loads(text)
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        raise
        except Exception as e:
            print(f"Extraction error: {e}")
            return {}
    
    async def _handle_select_movie(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Step 1: Select movie"""
        
        # Extract movie name from message
        extraction_prompt = f"""Trích xuất TÊN PHIM CHÍNH XÁC từ tin nhắn:
"{message}"

Trả về JSON: {{"movie_name": "tên phim user nói"}}
Nếu user KHÔNG NÓI TÊN PHIM cụ thể, trả về {{"movie_name": null}}

KHÔNG tự đoán hoặc thêm tên phim."""
        
        result = await self._extract_with_retry(extraction_prompt)
        movie_name = result.get("movie_name") if isinstance(result, dict) else None
        
        if not movie_name:
            return {
                "response": """Bạn muốn đặt vé xem phim nào? 

Cho tôi biết TÊN CHÍNH XÁC của phim bạn muốn xem nhé! 🎬
(Ví dụ: "Avatar", "The Godfather", "Inception"...)

Tôi sẽ kiểm tra trong hệ thống xem phim đó có đang chiếu không.""",
                "agent": self.name,
                "metadata": {"step": "select_movie"}
            }
        
        # Search for the movie IN DATABASE
        movies = await api_client.search_movies(query=movie_name, limit=5)
        
        if not movies:
            return {
                "response": f"""❌ Xin lỗi, phim '{movie_name}' KHÔNG CÓ trong hệ thống của chúng tôi.

Có thể:
- Phim chưa được thêm vào database
- Tên phim bạn nhập không chính xác
- Phim không còn chiếu

Bạn có thể:
✅ Thử tìm phim khác: "Tìm phim hành động"
✅ Xem danh sách phim đang có: "Có những phim nào"
✅ Kiểm tra lại tên phim

Tôi chỉ đặt vé cho phim CÓ TRONG DATABASE nhé! 😊""",
                "agent": self.name,
                "metadata": {"step": "select_movie", "movie_not_found": True}
            }
        
        # Found movie - check showtimes
        top_movie = movies[0]
        state.booking_state.movie_id = str(top_movie.get("id"))
        state.booking_state.movie_title = top_movie.get("series_title")
        state.booking_state.step = "select_showtime"
        
        # Get REAL showtimes from database
        showtimes = await api_client.get_showtimes(movie_id=int(state.booking_state.movie_id))
        
        if not showtimes:
            return {
                "response": f"""✅ Phim '{state.booking_state.movie_title}' CÓ trong database!

❌ Nhưng hiện tại KHÔNG CÓ SUẤT CHIẾU nào đang mở.

Có thể:
- Phim chưa có lịch chiếu
- Các suất chiếu đã đóng
- Chưa cập nhật suất chiếu mới

Bạn muốn:
🔍 Tìm phim khác đang có suất chiếu?
📋 Xem danh sách phim đang chiếu?

Tôi chỉ đặt được vé cho suất chiếu CÓ THẬT nhé!""",
                "agent": self.name,
                "metadata": {"step": "select_movie", "movie_found": True, "no_showtimes": True}
            }
        
        # Format REAL showtimes
        showtimes_text = self._format_showtimes(showtimes[:5])
        
        response = f"""✅ Tìm thấy phim **{state.booking_state.movie_title}** trong hệ thống! 🎬

📊 Có {len(showtimes)} suất chiếu ĐANG MỞ:
{showtimes_text}

Bạn muốn xem suất nào? Cho tôi biết:
- Ngày muốn xem (VD: "hôm nay", "mai", "25/12")
- Hoặc giờ ưa thích (VD: "tối", "chiều", "7 giờ")

Tôi sẽ chọn suất phù hợp nhất trong DANH SÁCH TRÊN! 📅"""
        
        return {
            "response": response,
            "agent": self.name,
            "metadata": {
                "step": "select_showtime",
                "movie": state.booking_state.movie_title,
                "showtimes_count": len(showtimes)
            }
        }
    
    async def _handle_select_showtime(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Step 2: Select showtime"""
        
        # Get showtimes for the selected movie
        showtimes = await api_client.get_showtimes(movie_id=int(state.booking_state.movie_id))
        
        if not showtimes:
            state.booking_state.step = "select_movie"
            return {
                "response": "Xin lỗi, không tìm thấy suất chiếu. Bạn muốn chọn phim khác không?",
                "agent": self.name,
                "metadata": {"step": "select_movie", "error": "no_showtimes"}
            }
        
        # Use Gemini to match user's preference with showtimes
        showtimes_info = self._format_showtimes_for_matching(showtimes)
        
        matching_prompt = f"""Người dùng muốn: "{message}"

Các suất chiếu có sẵn:
{showtimes_info}

Chọn suất chiếu phù hợp nhất. Trả về JSON:
{{
    "showtime_index": 0,
    "reason": "lý do chọn"
}}

Nếu không rõ ý người dùng, chọn suất gần nhất."""
        
        try:
            max_retries = 2
            showtime_index = 0
            for attempt in range(max_retries):
                try:
                    response = self.matching_model.generate_content(matching_prompt)
                    
                    # Parse JSON
                    text = response.text.strip()
                    if text.startswith("```json"):
                        text = text[7:]
                    if text.startswith("```"):
                        text = text[3:]
                    if text.endswith("```"):
                        text = text[:-3]
                    text = text.strip()
                    
                    result = json.loads(text)
                    showtime_index = result.get("showtime_index", 0)
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        showtime_index = 0  # Default to first
                        break
        except:
            showtime_index = 0
        
        selected_showtime = showtimes[min(showtime_index, len(showtimes) - 1)]
        
        # Save showtime info
        state.booking_state.showtime_id = str(selected_showtime.get("id"))
        state.booking_state.showtime_info = selected_showtime
        state.booking_state.step = "select_seats"
        
        response = f"""Được rồi! Tôi đã chọn suất chiếu:

🎬 **{state.booking_state.movie_title}**
📅 Ngày: {selected_showtime.get('date', 'N/A')}
🕐 Giờ: {selected_showtime.get('time', 'N/A')}
🏛️ Rạp: {selected_showtime.get('cinema_name', 'N/A')}
🪑 Phòng: {selected_showtime.get('room_name', 'N/A')}

Bạn muốn đặt bao nhiêu ghế? (Ví dụ: 2 ghế, 3 vé...) 🎟️"""
        
        return {
            "response": response,
            "agent": self.name,
            "metadata": {
                "step": "select_seats",
                "showtime": selected_showtime
            }
        }
    
    async def _handle_select_seats(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Step 3: Select seats"""
        
        # Extract number of seats
        extraction_prompt = f"""Trích xuất số lượng ghế từ: "{message}"

Trả về JSON: {{"num_seats": 2}}
Nếu không rõ, trả về {{"num_seats": 1}}"""
        
        result = await self._extract_with_retry(extraction_prompt)
        num_seats = result.get("num_seats", 1) if isinstance(result, dict) else 1
        num_seats = max(1, min(num_seats, 10))  # Limit 1-10 seats
        
        # Get available seats
        showtime_id = int(state.booking_state.showtime_id)
        available_seats = await api_client.get_available_seats(showtime_id)
        
        if not available_seats or len(available_seats) < num_seats:
            return {
                "response": f"Xin lỗi, suất chiếu này không còn đủ {num_seats} ghế trống. Bạn có muốn chọn suất khác không?",
                "agent": self.name,
                "metadata": {"step": "select_seats", "error": "insufficient_seats"}
            }
        
        # Auto-select best seats (first available)
        selected_seats = available_seats[:num_seats]
        seat_ids = [seat.get("id") for seat in selected_seats]
        seat_names = [seat.get("seat_number") for seat in selected_seats]
        
        # Calculate total price
        total_price = sum(seat.get("price", 0) for seat in selected_seats)
        
        # Save selection
        state.booking_state.seat_ids = seat_ids
        state.booking_state.total_price = total_price
        state.booking_state.step = "confirm"
        
        response = f"""Hoàn tất! Tôi đã chọn {num_seats} ghế tốt nhất cho bạn:

🎬 **{state.booking_state.movie_title}**
📅 {state.booking_state.showtime_info.get('date')} - {state.booking_state.showtime_info.get('time')}
🏛️ {state.booking_state.showtime_info.get('cinema_name')} - {state.booking_state.showtime_info.get('room_name')}
🪑 Ghế: {', '.join(seat_names)}
💰 Tổng tiền: {total_price:,.0f} VNĐ

Xác nhận đặt vé không? (Có/Không) ✅"""
        
        return {
            "response": response,
            "agent": self.name,
            "metadata": {
                "step": "confirm",
                "seats": seat_names,
                "total_price": total_price
            }
        }
    
    async def _handle_confirm(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Step 4: Confirm and create booking"""
        
        message_lower = message.lower()
        
        # Check for confirmation
        if any(word in message_lower for word in ["có", "yes", "ok", "đồng ý", "xác nhận"]):
            response = f"""✅ Đặt vé thành công!

📋 Chi tiết booking:
🎬 Phim: {state.booking_state.movie_title}
📅 Suất chiếu: {state.booking_state.showtime_info.get('date')} - {state.booking_state.showtime_info.get('time')}
🏛️ Rạp: {state.booking_state.showtime_info.get('cinema_name')}
🪑 Ghế: {', '.join([str(sid) for sid in state.booking_state.seat_ids])}
💰 Tổng tiền: {state.booking_state.total_price:,.0f} VNĐ

🔗 Vui lòng click vào link dưới để thanh toán:
[Thanh toán ngay](#/payment/booking_id)

Cảm ơn bạn đã sử dụng dịch vụ! 🎉"""
            
            # Reset booking state
            state.booking_state = None
            
            return {
                "response": response,
                "agent": self.name,
                "metadata": {
                    "step": "completed",
                    "booking_created": True
                }
            }
        
        else:
            # Cancel booking
            state.booking_state = None
            
            return {
                "response": "Đã hủy đặt vé. Bạn cần gì thêm không? 😊",
                "agent": self.name,
                "metadata": {
                    "step": "cancelled"
                }
            }
    
    def _format_showtimes(self, showtimes: list) -> str:
        """Format showtimes for display"""
        formatted = []
        for i, showtime in enumerate(showtimes, 1):
            formatted.append(
                f"{i}. 📅 {showtime.get('date', 'N/A')} | "
                f"🕐 {showtime.get('time', 'N/A')} | "
                f"🏛️ {showtime.get('cinema_name', 'N/A')}"
            )
        return "\n".join(formatted)
    
    def _format_showtimes_for_matching(self, showtimes: list) -> str:
        """Format showtimes for Gemini matching"""
        formatted = []
        for i, showtime in enumerate(showtimes):
            formatted.append(
                f"Index {i}: {showtime.get('date')} {showtime.get('time')} - "
                f"{showtime.get('cinema_name')} - {showtime.get('room_name')}"
            )
        return "\n".join(formatted)