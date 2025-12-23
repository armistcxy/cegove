# app/agents/router_agent.py
from app.agents.base import BaseAgent
from app.models.agent_state import AgentState, AgentType
from app.services.gemini_service import gemini_service
from app.agents.movie_agent import MovieAgent
from app.agents.booking_agent import BookingAgent
from app.agents.context_agent import ContextAgent  # THÊM
from typing import Dict, Any
import json
import time

class RouterAgent(BaseAgent):
    """
    Router Agent - Điều phối và phân tích ý định người dùng
    
    Nhiệm vụ:
    - Phân tích tin nhắn của user
    - Route đến agent phù hợp (Movie hoặc Booking)
    - Xử lý các câu hỏi chung, chào hỏi
    - Kiểm tra input hợp lệ
    """
    
    def __init__(self):
        super().__init__("router")
        self.movie_agent = MovieAgent()
        self.booking_agent = BookingAgent()
        self.context_agent = ContextAgent()  # THÊM
        
        # System instruction cho intent analysis
        self.intent_instruction = """Bạn là trợ lý AI cho hệ thống đặt vé xem phim.

QUAN TRỌNG: Bạn CHỈ có quyền truy cập vào database phim và lịch chiếu CÓ SẴN.
KHÔNG được tự tạo ra phim, rạp, hoặc suất chiếu không tồn tại.

Nhiệm vụ của bạn:
1. Phân tích ý định của người dùng
2. Xác định agent phù hợp để xử lý:
   - "movie": Tìm kiếm phim TỒN TẠI trong database, gợi ý dựa trên dữ liệu CÓ SẴN
   - "booking": Đặt vé cho phim và suất chiếu TỒN TẠI trong hệ thống
   - "general": Chào hỏi, cảm ơn, hỏi về khả năng của hệ thống

Trả về JSON với format:
{
    "intent": "movie" | "booking" | "general",
    "confidence": 0.0-1.0,
    "extracted_info": {
        // Thông tin trích xuất được như tên phim, thể loại, ngày, v.v.
    }
}

Lưu ý:
- Nếu user hỏi về phim KHÔNG có trong database → trả lời thật
- Nếu user muốn đặt rạp/suất chiếu KHÔNG tồn tại → từ chối lịch sự
- CHỈ làm việc với dữ liệu THỰC TẾ từ API"""

        # System instruction cho general chat
        self.general_instruction = """Bạn là trợ lý thân thiện cho hệ thống đặt vé phim.

GIỚI HẠN CHỨC NĂNG:
- Bạn CHỈ có thể tìm kiếm phim TỒN TẠI trong database
- Bạn CHỈ có thể đặt vé cho suất chiếu CÓ SẴN
- Bạn KHÔNG thể tự tạo ra phim, rạp, hoặc suất chiếu mới

Khi trả lời:
✅ Tìm kiếm phim trong database và gợi ý dựa trên kết quả TÌM được
✅ Đặt vé cho phim và suất chiếu TỒN TẠI
✅ Giải thích giới hạn khi user yêu cầu điều không có

❌ KHÔNG tự nghĩ ra tên phim không có trong database
❌ KHÔNG tạo suất chiếu giả định
❌ KHÔNG hứa hẹn điều không làm được

Hãy giới thiệu:
"🎬 Tôi có thể giúp bạn:
- Tìm kiếm phim ĐANG CÓ trong hệ thống
- Gợi ý phim dựa trên sở thích (từ database có sẵn)
- Đặt vé cho các suất chiếu ĐANG MỞ

Tôi chỉ làm việc với dữ liệu thực tế từ rạp. Hãy hỏi tôi nhé!"

Trả lời bằng tiếng Việt, thành thật và hữu ích."""
        
        # Khởi tạo models một lần
        self.intent_model = gemini_service.create_model(self.intent_instruction)
        self.general_model = gemini_service.create_model(self.general_instruction)
    
    async def process(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Phân tích và route message"""
        
        if not message or len(message.strip()) == 0:
            return {
                "response": "Bạn chưa nhập gì cả. Hãy cho tôi biết bạn cần gì nhé!",
                "agent": self.name,
                "metadata": None
            }
        
        # Nếu đang trong booking flow
        if state.current_agent == AgentType.BOOKING and state.booking_state:
            return await self.booking_agent.process(message, state)
        
        # KIỂM TRA CONTEXT AGENT TRƯỚC - ƯU TIÊN CAO
        if await self.context_agent.can_handle(message, state):
            print(f"[Router] Routing to ContextAgent for: {message}")
            return await self.context_agent.process(message, state)
        
        # Phân tích intent
        try:
            intent_result = await self._analyze_intent(message, state)
        except Exception as e:
            print(f"[Router] Intent analysis failed: {e}, using rule-based")
            intent_result = self._rule_based_intent(message)
        
        intent = intent_result.get("intent", "general")
        confidence = intent_result.get("confidence", 0.5)
        extracted_info = intent_result.get("extracted_info", {})
        
        print(f"[Router] Intent: {intent}, Confidence: {confidence}")
        
        # Route theo intent
        if intent == "booking" and confidence > 0.7:  # Tăng threshold
            state.current_agent = AgentType.BOOKING
            state.context.update(extracted_info)
            return await self.booking_agent.process(message, state)
        
        elif intent == "movie" and confidence > 0.6:
            state.current_agent = AgentType.MOVIE
            state.context.update(extracted_info)
            return await self.movie_agent.process(message, state)
        
        else:
            return await self._handle_general(message, state)
    
    async def can_handle(self, message: str, state: AgentState) -> bool:
        """Router có thể handle tất cả messages"""
        return True
    
    def _rule_based_intent(self, message: str) -> Dict[str, Any]:
        """Rule-based intent - THÔNG MINH HƠN"""
        message_lower = message.lower()
        
        # BOOKING keywords - ƯU TIÊN CAO
        booking_keywords = ["đặt vé", "book", "mua vé", "đặt chỗ", "booking", "đặt giúp", "muốn đặt"]
        if any(word in message_lower for word in booking_keywords):
            return {"intent": "booking", "confidence": 0.95, "extracted_info": {}}
        
        # CONTEXT keywords - ƯU TIÊN VỪA
        context_keywords = [
            "danh sách", "vừa", "trước", "đó", "đây", "bạn nói", "bạn đề xuất",
            "phim đầu", "phim thứ", "cái đầu", "cái thứ", "chi tiết",
            "trong đó", "ở trên", "nội dung của", "thông tin về"
        ]
        if any(word in message_lower for word in context_keywords):
            return {"intent": "general", "confidence": 0.9, "extracted_info": {"type": "context_question"}}
        
        # MOVIE keywords - ƯU TIÊN THẤP
        movie_keywords = ["phim", "movie", "xem", "tìm", "gợi ý", "thể loại", "diễn viên", "đạo diễn"]
        if any(word in message_lower for word in movie_keywords):
            return {"intent": "movie", "confidence": 0.85, "extracted_info": {}}
        
        return {"intent": "general", "confidence": 0.9, "extracted_info": {}}
    
    async def _analyze_intent(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Phân tích intent của message - Có context để hiểu ngữ cảnh"""
        
        # Build context từ history (6 messages gần nhất - tăng từ 4)
        context = self._build_gemini_context(state.history[-6:] if len(state.history) > 0 else [])
        
        # THÊM context summary vào prompt
        context_summary = ""
        if state.history:
            last_assistant_msg = next(
                (msg for msg in reversed(state.history) if msg.get("role") == "assistant"),
                None
            )
            if last_assistant_msg:
                context_summary = f"\nCuộc trò chuyện gần nhất: Bot vừa nói về: {last_assistant_msg.get('content', '')[:200]}..."
        
        prompt = f"""Phân tích tin nhắn sau và xác định ý định:

Tin nhắn: "{message}"{context_summary}

QUAN TRỌNG:
- Nếu câu hỏi liên quan đến thông tin VỪA CUNG CẤP trong lịch sử → intent: "general" (để context agent xử lý)
- Nếu hỏi TÌM KIẾM MỚI về phim → intent: "movie"
- Nếu muốn ĐẶT VÉ → intent: "booking"

Ví dụ:
- "Chỉ đưa tên phim trong danh sách" → general (context-based)
- "Tìm phim khoa học viễn tưởng" → movie (new search)

Trả về JSON theo format đã định."""
        
        try:
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    # Sử dụng chat với history để model hiểu ngữ cảnh
                    chat = self.intent_model.start_chat(history=context)
                    response = chat.send_message(prompt)
                    
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
            print(f"Error analyzing intent: {e}")
            return self._rule_based_intent(message)
    
    async def _handle_general(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Xử lý các câu hỏi chung - Dùng model đã khởi tạo"""
        
        # Predefined responses cho các câu thường gặp
        greetings = ["xin chào", "hello", "hi", "chào", "hey"]
        if any(g in message.lower() for g in greetings):
            return {
                "response": """Xin chào! 👋 Tôi là trợ lý đặt vé phim thông minh.

Tôi có thể giúp bạn:
🎬 Tìm kiếm và gợi ý phim hay
🎟️ Đặt vé xem phim nhanh chóng

Bạn cần giúp gì?""",
                "agent": self.name,
                "metadata": {"intent": "greeting"}
            }
        
        thanks = ["cảm ơn", "thanks", "thank you", "cám ơn"]
        if any(t in message.lower() for t in thanks):
            return {
                "response": "Không có gì! Rất vui được giúp bạn. Bạn cần gì thêm không? 😊",
                "agent": self.name,
                "metadata": {"intent": "thanks"}
            }
        
        # Build context from history
        context = self._build_gemini_context(state.history[-6:] if len(state.history) > 0 else [])
        
        try:
            # Sử dụng model đã khởi tạo sẵn với context
            chat = self.general_model.start_chat(history=context)
            
            # Retry logic
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    response = chat.send_message(message)
                    return {
                        "response": response.text,
                        "agent": self.name,
                        "metadata": {"intent": "general"}
                    }
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        raise
        except Exception as e:
            print(f"Error in general chat: {e}")
            if "429" in str(e):
                return {
                    "response": "Hệ thống đang quá tải. Tôi có thể giúp bạn tìm phim hoặc đặt vé. Bạn cần gì?",
                    "agent": self.name,
                    "metadata": {"intent": "general"}
                }
            return {
                "response": "Tôi có thể giúp bạn tìm phim hoặc đặt vé. Bạn cần gì?",
                "agent": self.name,
                "metadata": {"intent": "general"}
            }
    
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