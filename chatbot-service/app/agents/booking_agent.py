# app/agents/booking_agent.py
from app.agents.base import BaseAgent
from app.models.agent_state import AgentState, BookingState, AgentType
from app.services.gemini_service import gemini_service
from app.services.api_client import api_client
from typing import Dict, Any, List, Optional
import json
import time
import re

class BookingAgent(BaseAgent):
    """
    Booking Agent - Chuyên về đặt vé
    Hỗ trợ: Scenario 4, 6, 8
    """
    
    def __init__(self):
        super().__init__("booking")
        
        self.extraction_instruction = """Bạn là trợ lý trích xuất thông tin đặt vé.

QUAN TRỌNG:
- Trích xuất TÊN PHIM từ message (bất kể viết hoa/thường, tiếng Việt/Anh)
- KHÔNG tự thêm thông tin không có

Ví dụ:
- "đặt vé Zootopia" → {"movie_name": "Zootopia"}
- "mua vé The Godfather" → {"movie_name": "The Godfather"}
- "đặt vé phim avatar 2" → {"movie_name": "avatar 2"}
- "book 2 vé Inception" → {"movie_name": "Inception", "num_seats": 2}
- "đặt phim này" → {"movie_name": null, "reference": "this"}
- "đặt 2 vé phim đó" → {"movie_name": null, "reference": "that", "num_seats": 2}

Trả về JSON:
{
    "movie_name": "tên phim" | null,
    "num_seats": số ghế | null,
    "reference": "this" | "that" | null nếu user dùng từ "này", "đó", "kia"
}"""
        
        self.extraction_model = gemini_service.create_model(self.extraction_instruction)
    
    async def process(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Xử lý quy trình đặt vé đa bước"""
        
        # Initialize booking state
        if not state.booking_state:
            state.booking_state = BookingState(step="select_movie")
        
        current_step = state.booking_state.step
        print(f"[BookingAgent] Current step: {current_step}, message: {message}")
        
        # SCENARIO 6: Check for change intent (NOT in select_movie or confirm_movie)
        if current_step not in ["select_movie", "confirm_movie"]:
            change_result = await self._check_change_intent(message, state)
            if change_result:
                return change_result
        
        # Process based on step
        handlers = {
            "select_movie": self._handle_select_movie,
            "confirm_movie": self._handle_confirm_movie,
            "select_showtime": self._handle_select_showtime,
            "select_seats": self._handle_select_seats,
            "confirm": self._handle_confirm
        }
        
        handler = handlers.get(current_step, self._handle_select_movie)
        return await handler(message, state)
    
    async def can_handle(self, message: str, state: AgentState) -> bool:
        """Check if can handle booking request"""
        keywords = ["đặt vé", "book", "mua vé", "đặt chỗ", "booking"]
        return any(kw in message.lower() for kw in keywords)
    
    async def _check_change_intent(self, message: str, state: AgentState) -> Optional[Dict]:
        """SCENARIO 6: Detect and handle change intent"""
        
        change_keywords = ["đổi", "thay đổi", "change", "à thôi", "hủy", "cancel"]
        message_lower = message.lower()
        
        if not any(kw in message_lower for kw in change_keywords):
            return None
        
        if not state.booking_state:
            return None
        
        # Extract what user wants to change
        extraction = await self._extract_info(message)
        
        # Update quantity
        if extraction.get("num_seats"):
            old_seats = state.booking_state.num_seats
            state.booking_state.num_seats = extraction["num_seats"]
            state.booking_state.seat_ids = None
            state.booking_state.step = "select_seats"
            
            return {
                "response": f"""✅ Đã cập nhật số vé: {old_seats} → {extraction['num_seats']} vé

Để tôi tìm {extraction['num_seats']} ghế phù hợp cho bạn...""",
                "agent": self.name,
                "metadata": {"action": "update_quantity"}
            }
        
        # Cancel booking
        if any(w in message_lower for w in ["hủy", "cancel", "không đặt", "thôi"]):
            state.booking_state = None
            state.current_agent = AgentType.ROUTER
            
            return {
                "response": "Đã hủy đặt vé. Bạn cần gì khác không? 😊",
                "agent": self.name,
                "metadata": {"action": "cancelled"}
            }
        
        return None
    
    async def _handle_select_movie(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Step 1: Select movie"""
        
        # Try AI extraction first
        extraction = await self._extract_info(message)
        movie_name = extraction.get("movie_name")
        
        print(f"[BookingAgent] AI extraction: {extraction}")
        
        # Check for reference words (này, đó, kia) - use context
        if not movie_name:
            reference = extraction.get("reference")
            if reference or self._has_reference_word(message):
                movie_name = self._get_movie_from_context(state)
                if movie_name:
                    print(f"[BookingAgent] Got movie from context: {movie_name}")
        
        # Fallback: simple extraction if AI fails
        if not movie_name:
            movie_name = self._extract_movie_name(message, state)
        
        print(f"[BookingAgent] Final movie_name: {movie_name}")
        
        if not movie_name:
            return {
                "response": """🎬 Bạn muốn đặt vé xem phim nào?

Cho tôi biết TÊN PHIM bạn muốn xem nhé!
(VD: "Đặt vé Avatar", "Mua vé The Godfather")

Tôi sẽ kiểm tra trong hệ thống xem phim có đang chiếu không.""",
                "agent": self.name,
                "metadata": {"step": "select_movie"}
            }
        
        # Save num_seats if extracted
        if extraction.get("num_seats"):
            state.booking_state.num_seats = extraction["num_seats"]
        
        # ========== LUÔN SEARCH MOVIE TRONG DB ĐỂ LẤY ID CHÍNH XÁC ==========
        movies = await api_client.search_movies(query=movie_name, limit=3)
        
        if not movies:
            # SCENARIO 7: Try fuzzy search
            fuzzy = await api_client.fuzzy_search_movie(movie_name)
            if fuzzy.get("found"):
                movie = fuzzy["movie"]
                # Save fuzzy match for confirmation
                state.booking_state.movie_id = str(movie.get("id"))
                state.booking_state.movie_title = movie.get("series_title")
                state.booking_state.step = "confirm_movie"
                
                print(f"[BookingAgent] Fuzzy match: {movie.get('series_title')} (ID: {movie.get('id')})")
                
                return {
                    "response": f"""🔍 Không tìm thấy "{movie_name}" chính xác.

Có phải bạn muốn xem **{fuzzy['matched_title']}**?

Trả lời "có" để tiếp tục đặt vé.""",
                    "agent": self.name,
                    "metadata": {"step": "confirm_movie", "fuzzy_match": True}
                }
            
            return {
                "response": f"""❌ Phim '{movie_name}' KHÔNG CÓ trong hệ thống.

Bạn có thể:
🔍 Thử tên phim khác
📋 Hỏi "có phim gì đang chiếu" để xem danh sách

⚠️ Tôi chỉ đặt vé cho phim CÓ TRONG DATABASE!""",
                "agent": self.name,
                "metadata": {"step": "select_movie", "movie_not_found": True}
            }
        
        # Found movie - GET ID FROM DB RESULT
        movie = movies[0]
        movie_id = movie.get("id")
        movie_title = movie.get("series_title")
        
        print(f"[BookingAgent] Found movie in DB: {movie_title} (ID: {movie_id})")
        
        state.booking_state.movie_id = str(movie_id)
        state.booking_state.movie_title = movie_title
        
        return await self._proceed_to_showtimes(state)
    
    def _has_reference_word(self, message: str) -> bool:
        """Check if message contains reference words"""
        reference_words = ["này", "đó", "kia", "trên", "vừa", "nãy", "đấy"]
        message_lower = message.lower()
        return any(w in message_lower for w in reference_words)
    
    def _get_movie_from_context(self, state: AgentState) -> Optional[str]:
        """Get movie name from context (last mentioned movie)"""
        
        # Check movie_context first (from MovieAgent)
        if state.movie_context and state.movie_context.movie_titles:
            # Return the first (most recently discussed) movie
            return state.movie_context.movie_titles[0]
        
        # Fallback: extract from history
        for msg in reversed(state.history[-5:]):
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                # Look for **MovieTitle** pattern
                match = re.search(r'\*\*([^*]+)\*\*\s*\(\d{4}\)', content)
                if match:
                    return match.group(1)
        
        return None
    
    async def _handle_confirm_movie(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle fuzzy match confirmation"""
        
        message_lower = message.lower()
        print(f"[BookingAgent] Confirming movie, message: {message_lower}")
        
        # User confirms
        if any(w in message_lower for w in ["có", "yes", "ok", "đúng", "phải", "ừ", "uh", "đúng rồi"]):
            return await self._proceed_to_showtimes(state)
        
        # User denies - go back to select movie
        state.booking_state = BookingState(step="select_movie")
        return {
            "response": "OK, bạn muốn đặt vé phim nào khác?",
            "agent": self.name,
            "metadata": {"step": "select_movie"}
        }
    
    async def _proceed_to_showtimes(self, state: AgentState) -> Dict[str, Any]:
        """Helper: Get showtimes and proceed"""
        
        showtimes = await api_client.get_showtimes(movie_id=int(state.booking_state.movie_id))
        
        if not showtimes:
            state.booking_state.step = "select_movie"
            return {
                "response": f"""✅ Phim **{state.booking_state.movie_title}** có trong database!

❌ Nhưng hiện KHÔNG CÓ suất chiếu nào.

Bạn muốn tìm phim khác?""",
                "agent": self.name,
                "metadata": {"step": "select_movie", "no_showtimes": True}
            }
        
        # Save showtimes and move to next step
        state.booking_state.available_showtimes = showtimes[:10]
        state.booking_state.step = "select_showtime"
        
        showtimes_text = self._format_showtimes(showtimes[:5])
        
        num_seats_info = ""
        if state.booking_state.num_seats:
            num_seats_info = f"\n🎟️ Số vé: {state.booking_state.num_seats}"
        
        return {
            "response": f"""✅ Đặt vé phim **{state.booking_state.movie_title}**! 🎬{num_seats_info}

📅 Có {len(showtimes)} suất chiếu đang mở:
{showtimes_text}

Bạn muốn xem suất nào? Cho tôi biết:
- Số thứ tự (VD: "suất 1", "cái thứ 2")
- Hoặc giờ ưa thích (VD: "tối", "7 giờ")""",
            "agent": self.name,
            "metadata": {"step": "select_showtime", "showtimes_count": len(showtimes)}
        }
    
    async def _handle_select_showtime(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Step 2: Select showtime"""
        
        showtimes = state.booking_state.available_showtimes or []
        
        if not showtimes:
            state.booking_state.step = "select_movie"
            return {
                "response": "Không có thông tin suất chiếu. Hãy chọn phim trước nhé!",
                "agent": self.name,
                "metadata": {"step": "select_movie"}
            }
        
        # Try to match user's choice
        selected_index = self._match_showtime_choice(message, showtimes)
        
        if selected_index is None:
            showtimes_text = self._format_showtimes(showtimes[:5])
            return {
                "response": f"""Tôi chưa hiểu bạn muốn chọn suất nào. Các suất có sẵn:

{showtimes_text}

Hãy nói rõ hơn (VD: "suất 1", "suất 19:00", "cái đầu tiên")""",
                "agent": self.name,
                "metadata": {"step": "select_showtime"}
            }
        
        selected = showtimes[selected_index]
        state.booking_state.showtime_id = str(selected.get("id"))
        state.booking_state.showtime_info = selected
        state.booking_state.step = "select_seats"
        
        # SCENARIO 8: Get seat availability
        seat_info = await api_client.get_available_seats_count(state.booking_state.showtime_id)
        
        return {
            "response": f"""✅ Đã chọn suất chiếu:

🎬 **{state.booking_state.movie_title}**
📅 {selected.get('start_time', 'N/A')}
🏛️ Rạp: {selected.get('cinema_name', 'N/A')}

🪑 Còn **{seat_info.get('total_available', 0)}** ghế trống
{self._format_seat_types(seat_info.get('by_type', {}))}

Bạn muốn đặt bao nhiêu vé? (VD: "2 vé", "3 ghế VIP")""",
            "agent": self.name,
            "metadata": {"step": "select_seats", "available_seats": seat_info}
        }
    
    async def _handle_select_seats(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Step 3: Select seats - SCENARIO 4, 8"""
        
        extraction = await self._extract_info(message)
        
        num_seats = extraction.get("num_seats") or state.booking_state.num_seats or 1
        num_seats = max(1, min(num_seats, 10))
        state.booking_state.num_seats = num_seats
        
        # Get available seats from DB
        seats = await api_client.get_showtime_seats_v2(state.booking_state.showtime_id)
        available = [s for s in seats if s.get("status_text", "").lower() == "available"]
        
        # SCENARIO 8: Check availability
        if len(available) < num_seats:
            other_showtimes = await api_client.get_showtimes(
                movie_id=int(state.booking_state.movie_id)
            )
            other_showtimes = [s for s in other_showtimes 
                             if str(s.get("id")) != state.booking_state.showtime_id]
            
            suggestion = ""
            if other_showtimes:
                suggestion = f"\n\n📅 Suất chiếu khác còn chỗ:\n{self._format_showtimes(other_showtimes[:3])}"
            
            return {
                "response": f"""❌ Suất này chỉ còn **{len(available)}** ghế trống, không đủ {num_seats} ghế.
{suggestion}

Bạn muốn:
1️⃣ Giảm số vé
2️⃣ Chọn suất khác""",
                "agent": self.name,
                "metadata": {"step": "select_seats", "insufficient_seats": True}
            }
        
        # Specific seats or auto-select
        seat_codes = extraction.get("seat_codes")
        
        if seat_codes:
            selected = []
            for code in seat_codes:
                for seat in available:
                    if seat.get("label", "").upper() == code.upper():
                        selected.append(seat)
                        break
            
            if len(selected) < len(seat_codes):
                return {
                    "response": f"""❌ Một số ghế bạn chọn không khả dụng.

Ghế còn trống: {', '.join([s.get('label') for s in available[:20]])}

Hãy chọn lại hoặc để tôi chọn tự động.""",
                    "agent": self.name,
                    "metadata": {"step": "select_seats"}
                }
        else:
            selected = available[:num_seats]
        
        total_price = sum(s.get("pricing", {}).get("amount", 0) for s in selected)
        
        state.booking_state.seat_ids = [s.get("id") for s in selected]
        state.booking_state.seat_names = [s.get("label") for s in selected]
        state.booking_state.total_price = total_price
        state.booking_state.step = "confirm"
        
        return {
            "response": f"""✅ Đã chọn ghế thành công!

📋 **THÔNG TIN ĐẶT VÉ**
━━━━━━━━━━━━━━━━━
🎬 Phim: **{state.booking_state.movie_title}**
📅 Suất: {state.booking_state.showtime_info.get('start_time')}
🏛️ Rạp: {state.booking_state.showtime_info.get('cinema_name')}
🪑 Ghế: {', '.join(state.booking_state.seat_names)}
💰 Tổng tiền: **{total_price:,.0f} VNĐ**
━━━━━━━━━━━━━━━━━

✅ Xác nhận đặt vé? (Có/Không)""",
            "agent": self.name,
            "metadata": {"step": "confirm", "total_price": total_price}
        }
    
    async def _handle_confirm(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Step 4: Confirm booking"""
        
        message_lower = message.lower()
        
        if any(w in message_lower for w in ["có", "yes", "ok", "đồng ý", "xác nhận", "confirm"]):
            booking = await api_client.create_booking(
                user_id=state.user_id,
                showtime_id=state.booking_state.showtime_id,
                seat_ids=state.booking_state.seat_ids
            )
            
            if booking:
                booking_id = booking.get("id", "N/A")
                
                response = f"""🎉 **ĐẶT VÉ THÀNH CÔNG!**

📋 Mã booking: **{booking_id}**
🎬 Phim: {state.booking_state.movie_title}
📅 Suất: {state.booking_state.showtime_info.get('start_time')}
🏛️ Rạp: {state.booking_state.showtime_info.get('cinema_name')}
🪑 Ghế: {', '.join(state.booking_state.seat_names)}
💰 Tổng tiền: {state.booking_state.total_price:,.0f} VNĐ

⏰ Vui lòng thanh toán trong 15 phút.

Cảm ơn bạn! 🙏"""
            else:
                response = """❌ Có lỗi khi tạo booking. Vui lòng thử lại.

Ghế có thể đã được người khác đặt trước."""
            
            state.booking_state = None
            state.current_agent = AgentType.ROUTER
            
            return {
                "response": response,
                "agent": self.name,
                "metadata": {"step": "completed", "booking": booking}
            }
        
        else:
            state.booking_state = None
            state.current_agent = AgentType.ROUTER
            
            return {
                "response": "Đã hủy đặt vé. Bạn cần gì thêm không? 😊",
                "agent": self.name,
                "metadata": {"step": "cancelled"}
            }
    
    async def _extract_info(self, message: str) -> Dict[str, Any]:
        """Extract booking info from message"""
        try:
            prompt = f"""Trích xuất thông tin đặt vé từ: "{message}"

Ví dụ:
- "đặt vé Zootopia" → {{"movie_name": "Zootopia"}}
- "mua 2 vé The Godfather" → {{"movie_name": "The Godfather", "num_seats": 2}}
- "đặt phim này" → {{"movie_name": null, "reference": "this"}}
- "đặt 2 vé phim đó" → {{"movie_name": null, "reference": "that", "num_seats": 2}}

Trả về JSON:"""
            
            response = self.extraction_model.generate_content(prompt)
            text = response.text.strip()
            
            if text.startswith("```"):
                text = re.sub(r'^```\w*\n?', '', text)
                text = re.sub(r'\n?```$', '', text)
            
            result = json.loads(text.strip())
            return result
        except Exception as e:
            print(f"[BookingAgent] AI extraction failed: {e}")
            return self._simple_extract(message)
    
    def _extract_movie_name(self, message: str, state: AgentState) -> Optional[str]:
        """Extract movie name from message using rules"""
        
        message_lower = message.lower()
        
        # Check for reference words first - use context
        if self._has_reference_word(message):
            movie_from_context = self._get_movie_from_context(state)
            if movie_from_context:
                return movie_from_context
        
        # Remove booking keywords to isolate movie name
        booking_patterns = [
            r'đặt\s*vé\s*(phim\s*)?',
            r'mua\s*vé\s*(phim\s*)?',
            r'book\s*(vé\s*)?(phim\s*)?',
            r'đặt\s*giúp\s*(vé\s*)?(phim\s*)?',
            r'muốn\s*đặt\s*(vé\s*)?(phim\s*)?',
            r'muốn\s*xem\s*(phim\s*)?',
            r'tôi\s*muốn\s*(đặt\s*)?(vé\s*)?(phim\s*)?',
        ]
        
        movie_name = message
        for pattern in booking_patterns:
            movie_name = re.sub(pattern, '', movie_name, flags=re.IGNORECASE)
        
        # Remove number patterns (e.g., "2 vé")
        movie_name = re.sub(r'\d+\s*(vé|ghế|chỗ)', '', movie_name, flags=re.IGNORECASE)
        
        # Remove common words that aren't movie names
        remove_words = ['này', 'đó', 'kia', 'tôi', 'mình', 'cho', 'xem', 'coi', 'đấy', 'trên', 'vừa', 'nãy']
        for word in remove_words:
            movie_name = re.sub(rf'\b{word}\b', '', movie_name, flags=re.IGNORECASE)
        
        # Clean up
        movie_name = movie_name.strip()
        movie_name = re.sub(r'\s+', ' ', movie_name)
        
        # Remove trailing punctuation
        movie_name = movie_name.rstrip('?!.,')
        
        # If empty or too short after cleanup, try context
        if not movie_name or len(movie_name) <= 1:
            return self._get_movie_from_context(state)
        
        print(f"[BookingAgent] Rule-based extraction: '{movie_name}'")
        return movie_name
    
    def _simple_extract(self, message: str) -> Dict[str, Any]:
        """Simple extraction fallback"""
        result = {}
        message_lower = message.lower()
        
        # Extract number of seats
        match = re.search(r'(\d+)\s*(vé|ghế|chỗ|seats?)', message_lower)
        if match:
            result["num_seats"] = int(match.group(1))
        
        # Extract seat codes (A1, B2, etc.)
        codes = re.findall(r'\b([A-K]\d{1,2})\b', message.upper())
        if codes:
            result["seat_codes"] = codes
        
        # Check for reference words
        reference_words = ["này", "đó", "kia", "trên", "vừa"]
        if any(w in message_lower for w in reference_words):
            result["reference"] = "this"
        
        return result
    
    def _match_showtime_choice(self, message: str, showtimes: List[Dict]) -> Optional[int]:
        """Match user's showtime choice"""
        message_lower = message.lower()
        
        ordinals = {
            "1": 0, "2": 1, "3": 2, "4": 3, "5": 4,
            "đầu": 0, "thứ nhất": 0, "một": 0, "suất 1": 0,
            "thứ hai": 1, "hai": 1, "suất 2": 1,
            "thứ ba": 2, "ba": 2, "suất 3": 2,
            "thứ tư": 3, "bốn": 3, "suất 4": 3,
            "thứ năm": 4, "năm": 4, "suất 5": 4
        }
        
        for key, idx in ordinals.items():
            if key in message_lower and idx < len(showtimes):
                return idx
        
        # Match by time
        time_match = re.search(r'(\d{1,2})[:\.]?(\d{2})?', message)
        if time_match:
            hour = int(time_match.group(1))
            for i, st in enumerate(showtimes):
                st_time = st.get("start_time", "")
                if str(hour) in st_time:
                    return i
        
        return None
    
    def _format_showtimes(self, showtimes: List[Dict]) -> str:
        """Format showtimes list"""
        lines = []
        for i, st in enumerate(showtimes, 1):
            start_time = st.get('start_time', 'N/A')
            if "T" in str(start_time):
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    start_time = dt.strftime("%H:%M %d/%m")
                except:
                    pass
            
            lines.append(
                f"{i}️⃣ {start_time} - "
                f"🏛️ {st.get('cinema_name', 'Rạp')} - "
                f"💰 {st.get('base_price', 0):,.0f}đ"
            )
        return "\n".join(lines)
    
    def _format_seat_types(self, by_type: Dict[str, int]) -> str:
        """Format seat availability by type"""
        if not by_type:
            return ""
        
        type_names = {"STANDARD": "Thường", "VIP": "VIP", "COUPLE": "Đôi"}
        lines = []
        for t, count in by_type.items():
            name = type_names.get(t, t)
            lines.append(f"  • {name}: {count} ghế")
        return "\n".join(lines)