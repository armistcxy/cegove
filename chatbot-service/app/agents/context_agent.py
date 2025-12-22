# app/agents/context_agent.py
from app.agents.base import BaseAgent
from app.models.agent_state import AgentState
from app.services.gemini_service import gemini_service
from typing import Dict, Any
import json
import time

class ContextAgent(BaseAgent):
    """
    Context Agent - Xử lý câu hỏi dựa trên ngữ cảnh
    
    Nhiệm vụ:
    - Phân tích lịch sử chat để hiểu câu hỏi follow-up
    - Trả lời dựa trên thông tin ĐÃ CUNG CẤP trong lịch sử
    - KHÔNG tìm kiếm mới, chỉ dùng dữ liệu CÓ SẴN trong context
    """
    
    def __init__(self):
        super().__init__("context")
        
        self.context_instruction = """Bạn là trợ lý trả lời câu hỏi dựa trên LỊCH SỬ CHAT.

NGUYÊN TẮC QUAN TRỌNG:
1. CHỈ sử dụng thông tin ĐÃ ĐƯỢC CUNG CẤP trong lịch sử chat
2. KHÔNG tìm kiếm thêm dữ liệu mới
3. KHÔNG tự bịa thông tin không có trong lịch sử
4. Nếu thông tin không có trong lịch sử → nói thật

Nhiệm vụ:
- Đọc lịch sử chat để tìm thông tin liên quan
- Trả lời câu hỏi dựa 100% vào lịch sử
- Trích xuất, tóm tắt, sắp xếp lại thông tin ĐÃ CÓ

Ví dụ:
User trước: "Gợi ý phim hành động"
Bot trước: "1. The Dark Knight 2. Inception 3. Avatar"
User hỏi: "Chỉ đưa tôi tên phim"
→ Trả lời: "The Dark Knight, Inception, Avatar"

Trả lời bằng tiếng Việt, chính xác dựa trên lịch sử."""
        
        self.context_model = gemini_service.create_model(self.context_instruction)
    
    async def process(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Xử lý câu hỏi dựa trên context"""
        
        # Build full context from history
        context = self._build_gemini_context(state.history)
        
        if not context:
            return {
                "response": "Chưa có lịch sử chat nào. Bạn hỏi gì đi, tôi sẽ nhớ để trả lời sau! 😊",
                "agent": self.name,
                "metadata": {"context_available": False}
            }
        
        prompt = f"""Câu hỏi mới: "{message}"

NHIỆM VỤ:
1. Xem lại TOÀN BỘ lịch sử chat ở trên
2. Tìm thông tin liên quan đến câu hỏi
3. Trả lời dựa 100% vào thông tin ĐÃ CÓ trong lịch sử
4. Nếu không tìm thấy thông tin → "Tôi chưa cung cấp thông tin đó trong cuộc trò chuyện này"

Trả lời ngắn gọn, chính xác."""
        
        try:
            chat = self.context_model.start_chat(history=context)
            
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    response = chat.send_message(prompt)
                    return {
                        "response": response.text,
                        "agent": self.name,
                        "metadata": {
                            "context_available": True,
                            "history_length": len(state.history)
                        }
                    }
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        raise
        except Exception as e:
            print(f"Error in context processing: {e}")
            return {
                "response": "Xin lỗi, tôi gặp sự cố khi xử lý. Bạn có thể hỏi lại không?",
                "agent": self.name,
                "metadata": {"error": str(e)}
            }
    
    async def can_handle(self, message: str, state: AgentState) -> bool:
        """Check if message is context-dependent"""
        context_keywords = [
            "danh sách", "vừa", "trước", "đó", "đây", "bạn nói",
            "bạn đề xuất", "bạn gợi ý", "phim thứ", "cái thứ",
            "trong đó", "trong này", "ở trên", "phía trên"
        ]
        message_lower = message.lower()
        
        # Must have context keywords AND have history
        has_keyword = any(keyword in message_lower for keyword in context_keywords)
        has_history = len(state.history) > 0
        
        return has_keyword and has_history
    
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