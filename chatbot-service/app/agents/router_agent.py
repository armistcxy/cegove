# app/agents/router_agent.py
from app.agents.base import BaseAgent
from app.models.agent_state import AgentState, AgentType
from app.services.gemini_service import gemini_service
from app.services.api_client import api_client
from app.agents.movie_agent import MovieAgent
from app.agents.booking_agent import BookingAgent
from app.agents.context_agent import ContextAgent
from typing import Dict, Any
import json
import time
import re

class RouterAgent(BaseAgent):
    """
    Router Agent - Điều phối và phân tích ý định người dùng
    
    Hỗ trợ tất cả 8 Scenarios:
    - Scenario 1: Truy vấn thông tin chi tiết phim
    - Scenario 2: Gợi ý phim theo yêu cầu
    - Scenario 3: Hỏi giá và suất chiếu
    - Scenario 4: Đặt vé đa bước
    - Scenario 5: Truy vấn dựa trên lịch sử
    - Scenario 6: Thay đổi ý định giữa chừng
    - Scenario 7: Xử lý lỗi ngữ pháp (Fuzzy Search)
    - Scenario 8: Kiểm tra tình trạng phòng
    """
    
    def __init__(self):
        super().__init__("router")
        self.movie_agent = MovieAgent()
        self.booking_agent = BookingAgent()
        self.context_agent = ContextAgent()
        
        # System instruction cho intent analysis
        self.intent_instruction = """Bạn là trợ lý AI cho hệ thống đặt vé xem phim.

NGUYÊN TẮC BẮT BUỘC:
1. KHÔNG BỊA ĐẶT - Chỉ làm việc với dữ liệu CÓ THẬT từ database
2. CĂN CỨ DỮ LIỆU - Mọi thông tin phải từ API
3. ĐA NGÔN NGỮ - Hỗ trợ Tiếng Việt, Tiếng Anh, và trộn lẫn

Phân tích ý định và xác định agent:
- "movie": Tìm kiếm phim, thông tin chi tiết, gợi ý phim (Scenario 1, 2)
- "booking": Đặt vé, chọn ghế, xem suất chiếu (Scenario 3, 4, 8)
- "context": Hỏi về thông tin VỪA NÓI, phim thứ N, lịch sử chat (Scenario 5)
- "showtime": Hỏi lịch chiếu, giá vé cụ thể (Scenario 3)
- "availability": Hỏi còn ghế không, ghế VIP (Scenario 8)
- "history": Hỏi lịch sử đặt vé cá nhân (Scenario 5)
- "general": Chào hỏi, cảm ơn, hỏi chức năng

Trả về JSON:
{
    "intent": "movie|booking|context|showtime|availability|history|general",
    "confidence": 0.0-1.0,
    "extracted_info": {
        "movie_name": "tên phim nếu có",
        "genre": "thể loại nếu có",
        "date": "ngày nếu có",
        "cinema": "rạp nếu có",
        "num_tickets": số vé nếu có,
        "seat_type": "loại ghế nếu có"
    }
}"""

        # System instruction cho general chat
        self.general_instruction = """Bạn là trợ lý thân thiện cho hệ thống đặt vé phim.

NGUYÊN TẮC:
✅ Tìm kiếm phim TRONG DATABASE
✅ Đặt vé cho suất chiếu CÓ SẴN
✅ Trả lời thật khi không có dữ liệu

❌ KHÔNG tự bịa phim/rạp/suất chiếu
❌ KHÔNG hứa điều không làm được

Hỗ trợ:
🎬 Tìm phim theo tên, thể loại, đạo diễn
📅 Xem lịch chiếu và giá vé
🎟️ Đặt vé và chọn ghế
📊 Xem lịch sử đặt vé

Trả lời bằng tiếng Việt, thân thiện."""
        
        # Khởi tạo models
        self.intent_model = gemini_service.create_model(self.intent_instruction)
        self.general_model = gemini_service.create_model(self.general_instruction)
    
    async def process(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Phân tích và route message - Hỗ trợ tất cả scenarios"""
        
        # Empty check
        if not message or len(message.strip()) == 0:
            return {
                "response": "Bạn chưa nhập gì cả. Hãy cho tôi biết bạn cần gì nhé!",
                "agent": self.name,
                "metadata": None
            }
        
        message_lower = message.lower()
        
        # === SCENARIO 6: Kiểm tra thay đổi ý định giữa booking flow ===
        if state.current_agent == AgentType.BOOKING and state.booking_state:
            # Check if user wants to change/cancel
            change_keywords = ["đổi", "thay đổi", "change", "hủy", "cancel", "không", "thôi", "quay lại"]
            if any(kw in message_lower for kw in change_keywords):
                return await self._handle_booking_change(message, state)
            
            # Continue booking flow
            return await self.booking_agent.process(message, state)
        
        # === SCENARIO 5: Context-based questions (ƯU TIÊN CAO) ===
        if await self.context_agent.can_handle(message, state):
            print(f"[Router] Routing to ContextAgent for: {message}")
            return await self.context_agent.process(message, state)
        
        # === SCENARIO 8: Real-time availability check ===
        availability_keywords = ["còn ghế", "còn chỗ", "còn bao nhiêu", "ghế vip", "ghế thường", "hết chưa"]
        if any(kw in message_lower for kw in availability_keywords):
            return await self._handle_availability_check(message, state)
        
        # === SCENARIO 5: User booking history ===
        history_keywords = ["lịch sử", "đã đặt", "đã xem", "tuần trước", "tháng trước", "vé của tôi"]
        if any(kw in message_lower for kw in history_keywords):
            return await self._handle_user_history(message, state)
        
        # === Phân tích intent ===
        try:
            intent_result = await self._analyze_intent(message, state)
        except Exception as e:
            print(f"[Router] Intent analysis failed: {e}, using rule-based")
            intent_result = self._rule_based_intent(message)
        
        intent = intent_result.get("intent", "general")
        confidence = intent_result.get("confidence", 0.5)
        extracted_info = intent_result.get("extracted_info", {})
        
        print(f"[Router] Intent: {intent}, Confidence: {confidence}")
        
        # === Route theo intent ===
        
        # SCENARIO 4: Booking flow
        if intent == "booking" and confidence > 0.7:
            state.current_agent = AgentType.BOOKING
            state.context.update(extracted_info)
            return await self.booking_agent.process(message, state)
        
        # SCENARIO 3: Showtime/pricing inquiry (có thể dẫn đến booking)
        if intent == "showtime" and confidence > 0.6:
            return await self._handle_showtime_inquiry(message, state, extracted_info)
        
        # SCENARIO 1, 2: Movie search/info
        if intent == "movie" and confidence > 0.6:
            state.current_agent = AgentType.MOVIE
            state.context.update(extracted_info)
            return await self.movie_agent.process(message, state)
        
        # Default: General handler
        return await self._handle_general(message, state)
    
    async def can_handle(self, message: str, state: AgentState) -> bool:
        return True
    
    def _rule_based_intent(self, message: str) -> Dict[str, Any]:
        """Rule-based intent detection - Hỗ trợ tất cả scenarios"""
        message_lower = message.lower()
        extracted_info = {}
        
        # === BOOKING INTENT (Scenario 4) ===
        booking_keywords = ["đặt vé", "book", "mua vé", "đặt chỗ", "booking", "muốn đặt", "đặt giúp"]
        if any(word in message_lower for word in booking_keywords):
            return {"intent": "booking", "confidence": 0.95, "extracted_info": extracted_info}
        
        # === SHOWTIME/PRICING INTENT (Scenario 3) ===
        showtime_keywords = ["lịch chiếu", "suất chiếu", "giờ chiếu", "giá vé", "bảng giá", "mấy giờ", "chiếu lúc"]
        if any(word in message_lower for word in showtime_keywords):
            return {"intent": "showtime", "confidence": 0.9, "extracted_info": extracted_info}
        
        # === AVAILABILITY INTENT (Scenario 8) ===
        availability_keywords = ["còn ghế", "còn chỗ", "ghế vip", "ghế trống", "hết chưa", "còn không"]
        if any(word in message_lower for word in availability_keywords):
            return {"intent": "availability", "confidence": 0.9, "extracted_info": extracted_info}
        
        # === HISTORY INTENT (Scenario 5 - personal) ===
        history_keywords = ["lịch sử", "đã đặt", "đã xem", "vé của tôi", "booking của tôi"]
        if any(word in message_lower for word in history_keywords):
            return {"intent": "history", "confidence": 0.9, "extracted_info": extracted_info}
        
        # === CONTEXT INTENT (Scenario 5 - conversation) ===
        context_keywords = [
            "vừa", "trước đó", "ở trên", "phim đầu", "phim thứ", 
            "bạn nói", "danh sách", "trong đó", "nội dung của"
        ]
        if any(word in message_lower for word in context_keywords):
            return {"intent": "context", "confidence": 0.9, "extracted_info": {"type": "context_question"}}
        
        # === MOVIE INTENT (Scenario 1, 2) ===
        movie_keywords = ["phim", "movie", "xem", "tìm", "gợi ý", "thể loại", "diễn viên", "đạo diễn", "nội dung"]
        if any(word in message_lower for word in movie_keywords):
            # Extract count if exists (Scenario 2)
            count_match = re.search(r'(\d+)\s*phim', message_lower)
            if count_match:
                extracted_info["count"] = int(count_match.group(1))
            
            return {"intent": "movie", "confidence": 0.85, "extracted_info": extracted_info}
        
        return {"intent": "general", "confidence": 0.9, "extracted_info": {}}
    
    async def _analyze_intent(self, message: str, state: AgentState) -> Dict[str, Any]:
        """AI-based intent analysis với context"""
        
        context = self._build_gemini_context(state.history[-6:] if state.history else [])
        
        # Add context summary
        context_summary = ""
        if state.history:
            last_msg = next((m for m in reversed(state.history) if m.get("role") == "assistant"), None)
            if last_msg:
                context_summary = f"\nContext: Bot vừa nói: {last_msg.get('content', '')[:200]}..."
        
        prompt = f"""Phân tích tin nhắn: "{message}"{context_summary}

Xác định intent và trích xuất thông tin. Trả về JSON."""
        
        try:
            for attempt in range(2):
                try:
                    chat = self.intent_model.start_chat(history=context)
                    response = chat.send_message(prompt)
                    
                    text = response.text.strip()
                    # Clean JSON
                    if "```json" in text:
                        text = text.split("```json")[1].split("```")[0]
                    elif "```" in text:
                        text = text.split("```")[1].split("```")[0]
                    
                    return json.loads(text.strip())
                except Exception as e:
                    if "429" in str(e) and attempt == 0:
                        time.sleep(2)
                    else:
                        raise
        except Exception as e:
            print(f"[Router] AI intent error: {e}")
            return self._rule_based_intent(message)
    
    async def _handle_showtime_inquiry(self, message: str, state: AgentState, extracted_info: Dict) -> Dict[str, Any]:
        """Handle showtime/pricing inquiry - Scenario 3"""
        
        # Extract movie name if mentioned
        movie_name = extracted_info.get("movie_name")
        date = extracted_info.get("date") or api_client.parse_date_from_text(message)
        
        if movie_name:
            # Search movie first
            movies = await api_client.search_movies(query=movie_name, limit=1)
            
            if not movies:
                # Try fuzzy search (Scenario 7)
                fuzzy_result = await api_client.fuzzy_search_movie(movie_name)
                if fuzzy_result.get("found"):
                    movies = [fuzzy_result["movie"]]
                    confirm_msg = f"🔍 Có phải bạn muốn tìm phim **{fuzzy_result['matched_title']}** không?\n\n"
                else:
                    return {
                        "response": f"❌ Không tìm thấy phim '{movie_name}' trong hệ thống.\n\nBạn có thể:\n- Kiểm tra lại tên phim\n- Tìm phim khác: 'Gợi ý phim hành động'",
                        "agent": self.name,
                        "metadata": {"intent": "showtime", "movie_not_found": True}
                    }
            else:
                confirm_msg = ""
            
            movie = movies[0]
            movie_id = movie.get("id")
            
            # Get showtimes
            showtimes = await api_client.get_showtimes(movie_id=int(movie_id), date=date)
            
            if not showtimes:
                return {
                    "response": f"""{confirm_msg}📽️ Phim **{movie.get('series_title')}** hiện không có suất chiếu{f' ngày {date}' if date else ''}.

Bạn muốn:
🔍 Xem suất chiếu ngày khác?
🎬 Tìm phim khác đang chiếu?""",
                    "agent": self.name,
                    "metadata": {"intent": "showtime", "no_showtimes": True}
                }
            
            # Format showtimes
            showtimes_text = self._format_showtimes(showtimes[:8])
            
            return {
                "response": f"""{confirm_msg}📅 **Lịch chiếu phim {movie.get('series_title')}**{f' ngày {date}' if date else ''}:

{showtimes_text}

💡 Muốn đặt vé? Nói "Đặt vé suất [số]" hoặc "Đặt vé lúc [giờ]" nhé!""",
                "agent": self.name,
                "metadata": {
                    "intent": "showtime",
                    "movie_id": movie_id,
                    "showtimes_count": len(showtimes)
                }
            }
        
        # No movie specified - show general info or ask
        return {
            "response": """Bạn muốn xem lịch chiếu phim nào?

Hãy cho tôi biết:
- Tên phim (VD: "Lịch chiếu phim Avatar")
- Hoặc ngày cụ thể (VD: "Phim gì chiếu hôm nay")

Tôi sẽ kiểm tra trong hệ thống nhé! 🎬""",
            "agent": self.name,
            "metadata": {"intent": "showtime", "need_movie_name": True}
        }
    
    async def _handle_availability_check(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle seat availability check - Scenario 8"""
        
        # Check if in booking flow with showtime selected
        if state.booking_state and state.booking_state.showtime_id:
            showtime_id = state.booking_state.showtime_id
            showtime_info = state.booking_state.showtime_info or {}
            
            # Get real-time availability
            availability = await api_client.get_available_seats_count(showtime_id)
            
            if availability.get("error"):
                return {
                    "response": "❌ Không thể kiểm tra ghế lúc này. Vui lòng thử lại sau.",
                    "agent": self.name,
                    "metadata": {"error": availability.get("error")}
                }
            
            total = availability.get("total_available", 0)
            by_type = availability.get("by_type", {})
            
            if total == 0:
                # Suggest alternative showtimes
                movie_id = state.booking_state.movie_id
                if movie_id:
                    other_showtimes = await api_client.get_showtimes(movie_id=int(movie_id))
                    other_showtimes = [s for s in other_showtimes if str(s.get("id")) != showtime_id]
                    
                    if other_showtimes:
                        alt_text = self._format_showtimes(other_showtimes[:3])
                        return {
                            "response": f"""❌ Suất chiếu này đã **HẾT GHẾ**!

📽️ Các suất chiếu khác của phim này:
{alt_text}

Bạn muốn chọn suất khác không?""",
                            "agent": self.name,
                            "metadata": {"sold_out": True, "alternatives": len(other_showtimes)}
                        }
                
                return {
                    "response": "❌ Suất chiếu này đã **HẾT GHẾ**. Bạn muốn chọn phim/suất khác không?",
                    "agent": self.name,
                    "metadata": {"sold_out": True}
                }
            
            # Format availability by type
            type_info = "\n".join([f"  • {t}: {c} ghế" for t, c in by_type.items()])
            
            return {
                "response": f"""✅ Suất chiếu hiện còn **{total} ghế trống**:

{type_info}

Bạn muốn đặt bao nhiêu ghế?""",
                "agent": self.name,
                "metadata": {"available": total, "by_type": by_type}
            }
        
        # Not in booking flow
        return {
            "response": """Để kiểm tra ghế trống, bạn cần chọn suất chiếu trước.

Bạn muốn:
🎬 "Lịch chiếu phim [tên phim]"
🎟️ "Đặt vé phim [tên phim]"

Sau đó tôi sẽ cho bạn biết còn bao nhiêu ghế nhé!""",
            "agent": self.name,
            "metadata": {"need_showtime": True}
        }
    
    async def _handle_user_history(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle user booking history inquiry - Scenario 5"""
        
        user_id = state.user_id
        
        if user_id == "unknown":
            return {
                "response": "🔐 Bạn cần đăng nhập để xem lịch sử đặt vé.",
                "agent": self.name,
                "metadata": {"need_login": True}
            }
        
        # Get user's bookings
        bookings = await api_client.get_user_bookings(user_id)
        
        if not bookings:
            return {
                "response": """📋 Bạn chưa có lịch sử đặt vé nào.

Muốn đặt vé xem phim không? Hãy nói:
🎬 "Gợi ý phim hay"
🎟️ "Đặt vé phim [tên phim]" """,
                "agent": self.name,
                "metadata": {"no_bookings": True}
            }
        
        # Format booking history
        history_text = ""
        for i, booking in enumerate(bookings[:5], 1):
            status_emoji = "✅" if booking.get("status") == 1 else "⏳"
            tickets = booking.get("tickets", [])
            movie_title = tickets[0].get("movie_title", "N/A") if tickets else "N/A"
            showtime = tickets[0].get("showtime", "N/A") if tickets else "N/A"
            
            history_text += f"""{i}. {status_emoji} **{movie_title}**
   📅 {showtime}
   🎟️ {len(tickets)} vé | 💰 {booking.get('total_price', 0):,.0f} VNĐ

"""
        
        return {
            "response": f"""📋 **Lịch sử đặt vé của bạn:**

{history_text}
Tổng: {len(bookings)} booking

Bạn cần xem chi tiết booking nào không?""",
            "agent": self.name,
            "metadata": {"bookings_count": len(bookings)}
        }
    
    async def _handle_booking_change(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle booking change/cancel - Scenario 6"""
        
        message_lower = message.lower()
        
        # Cancel completely
        cancel_keywords = ["hủy", "cancel", "thôi", "không đặt", "bỏ"]
        if any(kw in message_lower for kw in cancel_keywords):
            state.reset_booking()
            return {
                "response": """✅ Đã hủy quá trình đặt vé.

Bạn cần gì khác không?
🎬 Tìm phim mới
🎟️ Đặt vé phim khác""",
                "agent": self.name,
                "metadata": {"booking_cancelled": True}
            }
        
        # Change number of tickets
        ticket_match = re.search(r'(\d+)\s*(?:vé|ghế|ticket)', message_lower)
        if ticket_match:
            new_count = int(ticket_match.group(1))
            if state.booking_state:
                state.booking_state.num_seats = new_count
                state.booking_state.seat_ids = None  # Reset seat selection
                state.booking_state.step = "select_seats"
                
                return {
                    "response": f"""✅ Đã đổi thành **{new_count} vé**.

Tiếp tục chọn ghế cho suất chiếu này nhé!""",
                    "agent": self.name,
                    "metadata": {"tickets_changed": new_count}
                }
        
        # Change cinema/showtime
        change_showtime_keywords = ["đổi suất", "suất khác", "giờ khác", "rạp khác"]
        if any(kw in message_lower for kw in change_showtime_keywords):
            if state.booking_state:
                state.booking_state.showtime_id = None
                state.booking_state.showtime_info = None
                state.booking_state.seat_ids = None
                state.booking_state.step = "select_showtime"
                
                # Get new showtimes
                movie_id = state.booking_state.movie_id
                if movie_id:
                    showtimes = await api_client.get_showtimes(movie_id=int(movie_id))
                    showtimes_text = self._format_showtimes(showtimes[:5])
                    
                    return {
                        "response": f"""✅ Đã reset suất chiếu. Chọn suất mới:

{showtimes_text}

Bạn muốn xem suất nào?""",
                        "agent": self.name,
                        "metadata": {"showtime_reset": True}
                    }
        
        # Unknown change - ask for clarification
        return {
            "response": """Bạn muốn thay đổi gì?

🔢 Số vé: "Đổi thành 4 vé"
⏰ Suất chiếu: "Đổi suất khác"
❌ Hủy: "Hủy đặt vé"

Hoặc tiếp tục đặt vé?""",
            "agent": self.name,
            "metadata": {"change_requested": True}
        }
    
    async def _handle_general(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle general questions"""
        
        message_lower = message.lower()
        
        # Greetings
        greetings = ["xin chào", "hello", "hi", "chào", "hey"]
        if any(g in message_lower for g in greetings):
            return {
                "response": """Xin chào! 👋 Tôi là trợ lý đặt vé phim.

Tôi có thể giúp bạn:
🎬 Tìm kiếm và gợi ý phim (từ database thật)
📅 Xem lịch chiếu và giá vé
🎟️ Đặt vé nhanh chóng
📊 Xem lịch sử đặt vé

Bạn muốn làm gì?""",
                "agent": self.name,
                "metadata": {"intent": "greeting"}
            }
        
        # Thanks
        thanks = ["cảm ơn", "thanks", "thank you", "cám ơn"]
        if any(t in message_lower for t in thanks):
            return {
                "response": "Không có gì! Rất vui được giúp bạn. Bạn cần gì thêm không? 😊",
                "agent": self.name,
                "metadata": {"intent": "thanks"}
            }
        
        # Use AI for other general questions
        context = self._build_gemini_context(state.history[-6:] if state.history else [])
        
        try:
            chat = self.general_model.start_chat(history=context)
            
            for attempt in range(2):
                try:
                    response = chat.send_message(message)
                    return {
                        "response": response.text,
                        "agent": self.name,
                        "metadata": {"intent": "general"}
                    }
                except Exception as e:
                    if "429" in str(e) and attempt == 0:
                        time.sleep(2)
                    else:
                        raise
        except Exception as e:
            print(f"[Router] General chat error: {e}")
            return {
                "response": """Tôi có thể giúp bạn:
🎬 Tìm phim: "Gợi ý phim hành động"
🎟️ Đặt vé: "Đặt vé phim Avatar"
📅 Lịch chiếu: "Lịch chiếu phim Inception"

Bạn cần gì?""",
                "agent": self.name,
                "metadata": {"intent": "general", "fallback": True}
            }
    
    def _format_showtimes(self, showtimes: list) -> str:
        """Format showtimes for display"""
        if not showtimes:
            return "Không có suất chiếu"
        
        formatted = []
        for i, st in enumerate(showtimes, 1):
            start_time = st.get("start_time", "N/A")
            # Parse time if it's ISO format
            if "T" in str(start_time):
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    start_time = dt.strftime("%H:%M %d/%m")
                except:
                    pass
            
            price = st.get("base_price", 0)
            formatted.append(f"{i}. 🕐 {start_time} | 💰 {price:,.0f}đ")
        
        return "\n".join(formatted)
    
    def _build_gemini_context(self, history: list) -> list:
        """Convert history to Gemini format"""
        gemini_history = []
        for msg in history:
            role = "model" if msg["role"] == "assistant" else "user"
            gemini_history.append({
                "role": role,
                "parts": [msg["content"]]
            })
        return gemini_history