# app/agents/router_agent.py
from app.agents.base import BaseAgent
from app.models.agent_state import AgentState, AgentType
from app.services.gemini_service import gemini_service
from app.services.api_client import api_client
from app.services.knowledge_service import knowledge_service
from app.agents.movie_agent import MovieAgent
from app.agents.booking_agent import BookingAgent
from app.agents.context_agent import ContextAgent
from typing import Dict, Any, Optional
import json
import time
import re
import logging

# Setup logger with color
logger = logging.getLogger("RouterAgent")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '\033[92m[%(name)s]\033[0m %(levelname)s: %(message)s'
    ))
    logger.addHandler(handler)

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
        self.intent_instruction = """Bạn là trợ lý AI phân tích ý định người dùng cho hệ thống đặt vé phim.

NHIỆM VỤ: Phân loại câu hỏi và trích xuất thông tin chính xác.

PHÂN LOẠI Ý ĐỊNH:
- "showtime": Hỏi PHIM GÌ ĐANG CHIẾU, lịch chiếu, giá vé (kể cả không nói tên phim cụ thể)
- "movie": Tìm kiếm phim THEO TÊN hoặc THỂ LOẠI cụ thể ("có phim Batman không", "phim hành động")
- "booking": Đặt vé, mua vé ("đặt vé", "book vé")
- "context": Hỏi về phim VỪA ĐỀ CẬP ("phim thứ 2", "cái đầu tiên")
- "cinema": Hỏi về rạp chiếu ("rạp ở đâu", "CGV nào")
- "general": Chào hỏi, cảm ơn, câu hỏi chung

QUAN TRỌNG - PHÂN BIỆT:
- "tôi muốn xem các phim đang chiếu" → showtime (hỏi DANH SÁCH phim đang chiếu)
- "có phim Batman không" → movie (tìm phim CỤ THỂ tên Batman)
- "phim hành động" → movie (tìm theo THỂ LOẠI)
- "lịch chiếu phim Avatar" → showtime + movie_name: "Avatar"

TRÍCH XUẤT MOVIE_NAME:
- CHỈ trích xuất TÊN PHIM THỰC SỰ
- "có phim Batman không" → movie_name: "Batman"
- "lịch chiếu The Godfather" → movie_name: "The Godfather"
- "phim gì đang chiếu" → movie_name: null (không có tên cụ thể)
- KHÔNG đưa các từ "có", "không", "nào", "gì", "đang" vào movie_name

Trả về JSON:
{
    "intent": "showtime|movie|booking|context|cinema|general",
    "confidence": 0.0-1.0,
    "extracted_info": {
        "movie_name": "TÊN PHIM CỤ THỂ hoặc null",
        "genre": "thể loại tiếng Anh nếu có",
        "date": "ngày nếu có"
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
        
        logger.info(f"{'='*60}")
        logger.info(f"ROUTER AGENT - Incoming message: '{message}'")
        logger.info(f"Session: {state.session_id}, User: {state.user_id}")
        logger.info(f"Current agent: {state.current_agent}")
        logger.info(f"Has booking_state: {state.booking_state is not None}")
        logger.info(f"Has focused_movie: {state.focused_movie.movie_title if state.focused_movie else 'None'}")
        
        # Empty check
        if not message or len(message.strip()) == 0:
            logger.warning("Empty message received")
            return {
                "response": "Bạn chưa nhập gì cả. Hãy cho tôi biết bạn cần gì nhé!",
                "agent": self.name,
                "metadata": None
            }
        
        message_lower = message.lower()
        
        # === SCENARIO 6: Kiểm tra thay đổi ý định giữa booking flow ===
        if state.current_agent == AgentType.BOOKING and state.booking_state:
            logger.info(f"📦 In BOOKING flow - step: {state.booking_state.step}")
            
            # Check if user wants to change/cancel
            change_keywords = ["đổi", "thay đổi", "change", "hủy", "cancel", "không", "thôi", "quay lại"]
            if any(kw in message_lower for kw in change_keywords):
                logger.info(f"⚠️ Change/cancel keyword detected in booking flow")
                return await self.booking_agent.process(message, state)
            
            # Check if user is asking a NEW question (not providing movie name)
            # These patterns indicate user wants info, not providing movie name
            exit_booking_patterns = [
                r"có phim (gì|nào)",      # "có phim gì đang chiếu"
                r"phim (gì|nào) đang",    # "phim gì đang chiếu"
                r"những phim.*chiếu",     # "những phim đang chiếu"
                r"các phim.*chiếu",       # "các phim đang chiếu"
                r"danh sách phim",        # "danh sách phim"
                r"gợi ý phim",            # "gợi ý phim"
                r"phim.*hot",             # "phim hot"
                r"phim.*hay",             # "phim hay"
                r"lịch chiếu",            # "lịch chiếu"
            ]
            if any(re.search(p, message_lower) for p in exit_booking_patterns):
                print(f"[Router] User asking info during booking, exiting booking flow")
                state.current_agent = AgentType.ROUTER
                state.booking_state = None
                # Re-route to appropriate handler
                # Don't return to booking, process as new query
            else:
                # Continue booking flow
                return await self.booking_agent.process(message, state)
        
        # === Check for SPECIFIC intents FIRST (before context) ===
        
        # Handle "phim hot", "phim hay" BEFORE showtime check
        vague_movie_patterns = ["phim.*hot", "phim.*hay", "phim nào hay", "có phim gì", "có phim nào"]
        if any(re.search(p, message_lower) for p in vague_movie_patterns):
            logger.info(f"🌟 Vague movie request detected: {message}")
            # Route to _handle_general which has better movie suggestion
            return await self._handle_general(message, state)
        
        # Showtime keywords - HIGH PRIORITY (but more specific)
        # "đang chiếu" alone is showtime, but "phim nào hot" is NOT
        showtime_patterns = [
            r"lịch chiếu",           # explicit showtime
            r"suất chiếu",           # explicit showtime
            r"phim gì chiếu",        # what's showing
            r"chiếu phim gì",        # what's showing
            r"phim nào chiếu",       # what's showing  
            r"các phim đang chiếu",  # movies currently showing
            r"những phim đang chiếu" # movies currently showing
        ]
        if any(re.search(p, message_lower) for p in showtime_patterns):
            logger.info(f"📅 SHOWTIME query detected: {message}")
            intent_result = self._rule_based_intent(message)
            return await self._handle_showtime_inquiry(message, state, intent_result.get("extracted_info", {}))
        
        # Booking keywords - HIGH PRIORITY  
        booking_patterns = ["đặt.*vé", "mua.*vé", "book.*vé", "đặt cho.*vé"]
        if any(re.search(p, message_lower) for p in booking_patterns):
            logger.info(f"🎫 BOOKING pattern detected: {message}")
            logger.info(f"   Has focused_movie: {state.focused_movie.movie_title if state.focused_movie else 'None'}")
            state.current_agent = AgentType.BOOKING
            return await self.booking_agent.process(message, state)
        
        # === SCENARIO 5: Context-based questions (ONLY for true context refs) ===
        if await self.context_agent.can_handle(message, state):
            logger.info(f"📚 CONTEXT query detected: {message}")
            return await self.context_agent.process(message, state)
        
        # === SCENARIO 8: Real-time availability check ===
        availability_keywords = ["còn ghế", "còn chỗ", "còn bao nhiêu", "ghế vip", "ghế thường", "hết chưa"]
        if any(kw in message_lower for kw in availability_keywords):
            return await self._handle_availability_check(message, state)
        
        # === SCENARIO 5: User booking history ===
        history_keywords = ["lịch sử", "đã đặt", "đã xem", "tuần trước", "tháng trước", "vé của tôi"]
        if any(kw in message_lower for kw in history_keywords):
            logger.info(f"📜 HISTORY query detected")
            return await self._handle_user_history(message, state)
        
        # === Phân tích intent ===
        logger.debug(f"Analyzing intent with AI...")
        try:
            intent_result = await self._analyze_intent(message, state)
        except Exception as e:
            logger.warning(f"Intent analysis failed: {e}, using rule-based")
            intent_result = self._rule_based_intent(message)
        
        intent = intent_result.get("intent", "general")
        confidence = intent_result.get("confidence", 0.5)
        extracted_info = intent_result.get("extracted_info", {})
        
        logger.info(f"🎯 Intent analysis result:")
        logger.info(f"   Intent: {intent}")
        logger.info(f"   Confidence: {confidence}")
        logger.info(f"   Extracted: {extracted_info}")
        
        # === Route theo intent ===
        
        # SCENARIO 4: Booking flow
        if intent == "booking" and confidence > 0.7:
            logger.info(f"→ Routing to BOOKING agent")
            state.current_agent = AgentType.BOOKING
            state.context.update(extracted_info)
            return await self.booking_agent.process(message, state)
        
        # SCENARIO 3: Showtime/pricing inquiry (có thể dẫn đến booking)
        if intent == "showtime" and confidence > 0.6:
            logger.info(f"→ Routing to SHOWTIME handler")
            return await self._handle_showtime_inquiry(message, state, extracted_info)
        
        # SCENARIO 1, 2: Movie search/info
        if intent == "movie" and confidence > 0.6:
            logger.info(f"→ Routing to MOVIE agent")
            state.current_agent = AgentType.MOVIE
            state.context.update(extracted_info)
            return await self.movie_agent.process(message, state)
        
        # CINEMA: Cinema queries
        if intent == "cinema" and confidence > 0.6:
            return await self._handle_cinema_query(message, state, extracted_info)
        
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
        showtime_keywords = ["lịch chiếu", "suất chiếu", "giờ chiếu", "giá vé", "bảng giá", "mấy giờ", "chiếu lúc", "chiếu hôm nay", "đang chiếu", "phim gì chiếu", "các phim chiếu", "phim nào chiếu"]
        # Also detect "muốn xem các phim đang chiếu" pattern
        showing_patterns = ["phim đang chiếu", "các phim đang", "những phim đang", "muốn xem.*đang chiếu"]
        is_showing_query = any(word in message_lower for word in showtime_keywords) or \
                           any(re.search(p, message_lower) for p in showing_patterns)
        
        if is_showing_query:
            # Try to extract movie name from message
            movie_name = self._extract_movie_name(message)
            if movie_name:
                extracted_info["movie_name"] = movie_name
            # Check for date
            date = api_client.parse_date_from_text(message)
            if date:
                extracted_info["date"] = date
            elif "hôm nay" in message_lower or "today" in message_lower:
                from datetime import datetime
                extracted_info["date"] = datetime.now().strftime("%Y-%m-%d")
            return {"intent": "showtime", "confidence": 0.95, "extracted_info": extracted_info}
        
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
        movie_keywords = ["phim", "movie", "tìm phim", "gợi ý", "thể loại", "diễn viên", "đạo diễn", "nội dung", "phim hay", "phim nào"]
        
        # Check for vague "xem phim" without specific movie - should be general
        vague_patterns = ["muốn xem phim", "muốn xem", "xem phim gì", "xem gì"]
        if any(p in message_lower for p in vague_patterns):
            return {"intent": "general", "confidence": 0.9, "extracted_info": {"type": "movie_suggestion_needed"}}
        
        if any(word in message_lower for word in movie_keywords):
            # Extract count if exists (Scenario 2)
            count_match = re.search(r'(\d+)\s*phim', message_lower)
            if count_match:
                extracted_info["count"] = int(count_match.group(1))
            
            # Extract movie name if searching for specific movie
            movie_name = self._extract_movie_name(message)
            if movie_name:
                extracted_info["movie_name"] = movie_name
            
            return {"intent": "movie", "confidence": 0.85, "extracted_info": extracted_info}
        
        # === CINEMA INTENT ===
        cinema_keywords = ["rạp", "cgv", "lotte", "cinema", "galaxy", "địa chỉ rạp", "rạp ở", "rạp nào"]
        if any(word in message_lower for word in cinema_keywords):
            # Extract city if exists
            cities = knowledge_service.get_unique_cities()
            for city in cities:
                if city.lower() in message_lower:
                    extracted_info["city"] = city
                    break
            return {"intent": "cinema", "confidence": 0.9, "extracted_info": extracted_info}
        
        return {"intent": "general", "confidence": 0.9, "extracted_info": {}}
    
    def _extract_movie_name(self, message: str) -> Optional[str]:
        """Extract movie name from message using patterns"""
        message_lower = message.lower()
        
        # Skip patterns - queries that DON'T have specific movie names
        skip_patterns = [
            r'(phim|các|những)\s*(gì|nào)?\s*đang\s*chiếu',  # "phim gì đang chiếu"
            r'lịch\s*chiếu\s*phim\s*(hôm\s*nay|ngày\s*mai|tuần|tháng)$',  # "lịch chiếu phim hôm nay"
            r'lịch\s*chiếu\s*(hôm\s*nay|ngày\s*mai)$',  # "lịch chiếu hôm nay"
            r'suất\s*chiếu\s*(hôm\s*nay|ngày\s*mai)$',  # "suất chiếu hôm nay"
            r'^lịch\s*chiếu\s*phim\s*$',  # just "lịch chiếu phim"
            r'^phim\s*(hôm\s*nay|ngày\s*mai|chiếu)$',  # "phim hôm nay", "phim chiếu"
            r'phim\s*(gì|nào)\s*(hay|hot)',  # "phim gì hay", "phim nào hot"
        ]
        
        for skip_pattern in skip_patterns:
            if re.search(skip_pattern, message_lower):
                return None
        
        # Words that are NOT movie names
        noise_words = [
            "gì", "nào", "hay", "hôm nay", "ngày mai", "này", "đó", "ở", "tại", 
            "đang", "các", "những", "chiếu", "hot", "mới", "phim", "vé"
        ]
        
        # Patterns to extract movie name - ORDER MATTERS (more specific first)
        # Use GREEDY matching (+) and then trim, rather than non-greedy (+?)
        patterns = [
            # "lịch chiếu phim Zootopia 2" → "Zootopia 2"
            # "lịch chiếu phim The Godfather hôm nay" → "The Godfather"
            r"lịch\s+chiếu\s+(?:phim\s+)?([A-Z][A-Za-z0-9\s:'\-]+?)(?:\s+hôm\s+nay|\s+ngày\s+mai|\s+ngày|\s+tại|\s+ở|$)",
            # "suất chiếu phim Avatar" → "Avatar"
            r"suất\s+chiếu\s+(?:phim\s+)?([A-Z][A-Za-z0-9\s:'\-]+?)(?:\s+hôm|\s+ngày|$)",
            # "phim The Dark Knight chiếu" → "The Dark Knight"
            r"phim\s+([A-Z][A-Za-z0-9\s:'\-]+?)(?:\s+chiếu|\s+có|\s+lịch|\s+suất|\s+giá)",
            # "đặt vé Inception" or "đặt vé phim Zootopia 2" → "Inception" / "Zootopia 2"
            r"đặt\s+vé\s+(?:phim\s+)?([A-Z][A-Za-z0-9\s:'\-]+?)(?:\s+lúc|\s+suất|$)",
            # "xem phim Avatar" → "Avatar"
            r"xem\s+(?:phim\s+)?([A-Z][A-Za-z0-9\s:'\-]+?)(?:\s+lúc|\s+chiếu|$)",
            # Vietnamese movie names: "phim Hai Phượng" → "Hai Phượng"
            r"phim\s+([A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ][a-zA-Z0-9ÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴàáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ\s]+?)(?:\s+chiếu|\s+có|\s+lịch|\s+suất|\s+giá|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                name = match.group(1).strip()
                # Clean trailing noise words
                for n in noise_words:
                    name = re.sub(rf'\s+{n}$', '', name, flags=re.IGNORECASE)
                # Validate: not a noise word and has reasonable length
                if name and name.lower() not in noise_words and len(name) > 1:
                    logger.debug(f"Extracted movie name: '{name}' from pattern: {pattern[:50]}...")
                    return name
        
        # Fallback: Try to extract anything after "phim" that looks like a title
        # "lịch chiếu phim Zootopia 2" - last resort
        fallback_match = re.search(r'(?:lịch\s+chiếu|suất\s+chiếu|đặt\s+vé|xem)\s+(?:phim\s+)?(.+)$', message, re.IGNORECASE)
        if fallback_match:
            name = fallback_match.group(1).strip()
            # Remove date suffixes
            name = re.sub(r'\s+(hôm\s+nay|ngày\s+mai|ngày\s+\d+).*$', '', name, flags=re.IGNORECASE)
            # Check if first char is uppercase (looks like a title)
            if name and name[0].isupper() and name.lower() not in noise_words and len(name) > 1:
                logger.debug(f"Extracted movie name (fallback): '{name}'")
                return name
        
        return None
    
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
        movie_name = extracted_info.get("movie_name") or self._extract_movie_name(message)
        date = extracted_info.get("date") or api_client.parse_date_from_text(message)
        
        # If asking "phim gì chiếu hôm nay" without specific movie
        message_lower = message.lower()
        
        # Patterns that mean "what movies are showing" (no specific movie name)
        asking_whats_showing_patterns = [
            "phim gì chiếu", "chiếu phim gì", "đang chiếu", "phim nào chiếu",
            "lịch chiếu phim hôm nay", "lịch chiếu hôm nay", "suất chiếu hôm nay",
            "lịch chiếu phim ngày", "phim chiếu hôm nay", "hôm nay chiếu phim",
            "có phim gì", "những phim chiếu", "các phim chiếu"
        ]
        asking_whats_showing = any(p in message_lower for p in asking_whats_showing_patterns)
        
        # Also check: if message is just "lịch chiếu phim" + date word without movie name
        if not asking_whats_showing and not movie_name:
            date_words = ["hôm nay", "ngày mai", "hôm qua", "tuần này", "cuối tuần"]
            has_date_word = any(d in message_lower for d in date_words)
            is_generic_showtime = re.search(r'^lịch\s*chiếu\s*(phim)?\s*', message_lower)
            if is_generic_showtime and has_date_word:
                asking_whats_showing = True
        
        if asking_whats_showing and not movie_name:
            # Get all showtimes for today
            if not date:
                from datetime import datetime
                date = datetime.now().strftime("%Y-%m-%d")
            
            showtimes = await api_client.get_showtimes(date=date)
            
            if not showtimes:
                return {
                    "response": f"📅 Không có suất chiếu nào cho ngày {date}.\n\nBạn muốn xem ngày khác không?",
                    "agent": self.name,
                    "metadata": {"intent": "showtime", "no_showtimes": True}
                }
            
            # Group by movie
            movies_showing = {}
            for st in showtimes:
                movie_id = st.get("movie_id")
                if movie_id not in movies_showing:
                    movies_showing[movie_id] = {
                        "movie_id": movie_id,
                        "showtimes": []
                    }
                movies_showing[movie_id]["showtimes"].append(st)
            
            # Get movie details and format
            response_lines = [f"🎬 **Phim đang chiếu ngày {date}:**\n"]
            for i, (movie_id, data) in enumerate(list(movies_showing.items())[:10], 1):
                movie = await api_client.get_movie_detail(movie_id)
                title = movie.get("series_title", f"Phim #{movie_id}") if movie else f"Phim #{movie_id}"
                num_shows = len(data["showtimes"])
                response_lines.append(f"{i}. **{title}** - {num_shows} suất chiếu")
            
            response_lines.append("\n💡 Nói \"Lịch chiếu phim [tên]\" để xem chi tiết!")
            
            return {
                "response": "\n".join(response_lines),
                "agent": self.name,
                "metadata": {"intent": "showtime", "movies_count": len(movies_showing)}
            }
        
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
            movie_title = movie.get("series_title")
            
            # Get showtimes
            showtimes = await api_client.get_showtimes(movie_id=int(movie_id), date=date)
            
            if not showtimes:
                return {
                    "response": f"""{confirm_msg}📽️ Phim **{movie_title}** hiện không có suất chiếu{f' ngày {date}' if date else ''}.

Bạn muốn:
🔍 Xem suất chiếu ngày khác?
🎬 Tìm phim khác đang chiếu?""",
                    "agent": self.name,
                    "metadata": {"intent": "showtime", "no_showtimes": True}
                }
            
            # *** SET FOCUSED MOVIE ***
            # Khi user xem lịch chiếu phim, set phim đó làm focused movie
            state.set_focused_movie(
                movie_id=str(movie_id),
                movie_title=movie_title,
                showtimes=showtimes
            )
            logger.info(f"🎯 SET FOCUSED MOVIE: {movie_title} (ID: {movie_id})")
            logger.info(f"   Showtimes loaded: {len(showtimes)}")
            
            # Format showtimes
            showtimes_text = self._format_showtimes(showtimes[:8])
            
            return {
                "response": f"""{confirm_msg}📅 **Lịch chiếu phim {movie_title}**{f' ngày {date}' if date else ''}:

{showtimes_text}

💡 Muốn đặt vé? Nói "Đặt vé suất [số]" hoặc "Đặt vé lúc [giờ]" nhé!""",
                "agent": self.name,
                "metadata": {
                    "intent": "showtime",
                    "movie_id": movie_id,
                    "movie_title": movie_title,
                    "showtimes_count": len(showtimes),
                    "focused_movie": movie_title
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
        
        # Greetings (có thể kèm theo request)
        greetings = ["xin chào", "hello", "hi", "chào", "hey"]
        has_greeting = any(g in message_lower for g in greetings)
        
        # Check if greeting + movie request (including "hot", "hay", etc.)
        movie_interest = ["phim", "xem", "hot", "hay", "chiếu"]
        if has_greeting and any(w in message_lower for w in movie_interest):
            # Get some movie suggestions
            movies = await api_client.get_movies(page=1, page_size=5, sort_by="imdb_rating")
            movies_list = movies.get("items", [])
            
            if movies_list:
                movie_text = "\n".join([f"{i}. **{m.get('series_title')}** ({m.get('released_year', 'N/A')}) - ⭐ {m.get('imdb_rating', 'N/A')}" for i, m in enumerate(movies_list, 1)])
                return {
                    "response": f"""Xin chào! 👋 Rất vui được hỗ trợ bạn!

🎬 **Một số phim hay đang có:**
{movie_text}

💡 Bạn muốn:
- Xem chi tiết phim nào? (VD: "Phim số 1")
- Xem lịch chiếu? (VD: "Lịch chiếu phim [tên]")
- Đặt vé? (VD: "Đặt vé phim [tên]")""",
                    "agent": self.name,
                    "metadata": {"intent": "greeting_with_movies"}
                }
        
        # Pure greeting
        if has_greeting:
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
        
        # Vague movie requests - suggest movies
        vague_movie = ["muốn xem phim", "muốn xem", "xem phim gì", "xem gì", "phim hay", "gợi ý phim", "phim hot", "phim nào hot", "phim gì hay", "có phim gì", "có phim nào"]
        if any(v in message_lower for v in vague_movie):
            movies = await api_client.get_movies(page=1, page_size=5, sort_by="imdb_rating")
            movies_list = movies.get("items", [])
            
            if movies_list:
                movie_text = "\n".join([f"{i}. **{m.get('series_title')}** ({m.get('released_year', 'N/A')}) - ⭐ {m.get('imdb_rating', 'N/A')}" for i, m in enumerate(movies_list, 1)])
                return {
                    "response": f"""🎬 **Gợi ý phim hay cho bạn:**

{movie_text}

💡 Bạn muốn:
- Xem chi tiết? Nói "Kể về phim số 1"
- Xem lịch chiếu? Nói "Lịch chiếu phim [tên]"
- Tìm thể loại khác? Nói "Phim hành động" hoặc "Phim kinh dị\"""",
                    "agent": self.name,
                    "metadata": {"intent": "movie_suggestion"}
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
🏢 Rạp chiếu: "Rạp ở Hà Nội"

Bạn cần gì?""",
                "agent": self.name,
                "metadata": {"intent": "general", "fallback": True}
            }
    
    async def _handle_cinema_query(self, message: str, state: AgentState, extracted_info: Dict) -> Dict[str, Any]:
        """Handle cinema-related queries"""
        message_lower = message.lower()
        
        # Check if asking about specific city
        city = extracted_info.get("city")
        if city:
            cinemas = knowledge_service.get_cinemas_by_city(city)
            if cinemas:
                cinema_list = knowledge_service.get_cinema_list_text(cinemas)
                return {
                    "response": f"🎬 **Danh sách rạp CGV tại {city}:**\n\n{cinema_list}",
                    "agent": self.name,
                    "metadata": {"intent": "cinema", "city": city, "count": len(cinemas)}
                }
            else:
                return {
                    "response": f"❌ Không tìm thấy rạp CGV tại {city}.\n\nCác thành phố có rạp: {', '.join(knowledge_service.get_unique_cities()[:10])}",
                    "agent": self.name,
                    "metadata": {"intent": "cinema", "city": city, "found": False}
                }
        
        # Check if asking about specific cinema by name
        cinema_patterns = [
            r"rạp\s+(.+?)(?:\s+có|\s+chiếu|\s+ở|$)",
            r"cgv\s+(.+?)(?:\s+có|\s+chiếu|\s+ở|$)",
            r"địa chỉ\s+(?:rạp\s+)?(.+?)$"
        ]
        
        for pattern in cinema_patterns:
            match = re.search(pattern, message_lower)
            if match:
                cinema_name = match.group(1).strip()
                cinemas = knowledge_service.search_cinema(cinema_name)
                if cinemas:
                    cinema = cinemas[0]
                    cinema_info = knowledge_service.format_cinema_info(cinema)
                    
                    # Check if user wants showtimes at this cinema
                    if "chiếu" in message_lower or "lịch" in message_lower:
                        showtimes = await api_client.get_showtimes(cinema_id=cinema.get("id"))
                        if showtimes:
                            st_text = self._format_showtimes(showtimes[:5])
                            return {
                                "response": f"{cinema_info}\n\n📅 **Lịch chiếu hôm nay:**\n{st_text}",
                                "agent": self.name,
                                "metadata": {"intent": "cinema", "cinema_id": cinema.get("id")}
                            }
                    
                    return {
                        "response": f"🏢 **Thông tin rạp:**\n\n{cinema_info}\n\n💡 Muốn xem lịch chiếu? Hỏi \"Rạp này chiếu phim gì?\"",
                        "agent": self.name,
                        "metadata": {"intent": "cinema", "cinema_id": cinema.get("id")}
                    }
        
        # Check if asking for all cinemas
        if "tất cả" in message_lower or "danh sách" in message_lower:
            all_cinemas = knowledge_service.cinemas
            cities = knowledge_service.get_unique_cities()
            
            return {
                "response": f"""🎬 **Hệ thống rạp CGV:**

📍 Tổng số rạp: {len(all_cinemas)}
🏙️ Các thành phố: {', '.join(cities[:10])}{'...' if len(cities) > 10 else ''}

💡 Để xem rạp theo thành phố, hỏi:
- "Rạp ở Hà Nội"
- "CGV Hồ Chí Minh"
- "Rạp ở Đà Nẵng\"""",
                "agent": self.name,
                "metadata": {"intent": "cinema", "total": len(all_cinemas)}
            }
        
        # Default: show available cities
        cities = knowledge_service.get_unique_cities()
        return {
            "response": f"""🎬 Bạn muốn tìm rạp chiếu phim?

📍 Các thành phố có rạp CGV:
{', '.join(cities[:10])}{'...' if len(cities) > 10 else ''}

💡 Ví dụ:
- "Rạp ở Hà Nội"
- "CGV Times City"
- "Địa chỉ rạp Vincom Đồng Khởi\"""",
            "agent": self.name,
            "metadata": {"intent": "cinema"}
        }
    
    def _format_showtimes(self, showtimes: list) -> str:
        """Format showtimes for display with cinema info"""
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
            
            # Get cinema name - from showtime data or lookup by ID
            cinema_name = st.get("cinema_name", "")
            cinema_id = st.get("cinema_id")
            
            if not cinema_name and cinema_id:
                cinema = knowledge_service.get_cinema_by_id(cinema_id)
                if cinema:
                    cinema_name = cinema.get("name", "")
                else:
                    # Fallback: show cinema_id if not found in knowledge base
                    cinema_name = f"Rạp #{cinema_id}"
            
            if cinema_name:
                formatted.append(f"{i}. 🕐 {start_time} | 🏢 {cinema_name} | 💰 {price:,.0f}đ")
            else:
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