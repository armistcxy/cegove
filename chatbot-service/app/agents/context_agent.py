# app/agents/context_agent.py - VERSION HOÀN CHỈNH
from app.agents.base import BaseAgent
from app.models.agent_state import AgentState
from app.services.gemini_service import gemini_service
from typing import Dict, Any
import re
import time

class ContextAgent(BaseAgent):
    """Context Agent - Xử lý câu hỏi dựa trên ngữ cảnh"""
    
    def __init__(self):
        super().__init__("context")
        
        # ĐƠN GIẢN HÓA - FOCUS VÀO EXTRACTION
        self.context_instruction = """Bạn là trợ lý trích xuất và tóm tắt thông tin từ lịch sử chat.

NHIỆM VỤ:
1. Đọc lịch sử chat
2. Tìm thông tin user hỏi
3. Trích xuất CHÍNH XÁC thông tin đó
4. Trả lời ngắn gọn

Ví dụ:
Lịch sử: "Top phim: The Father (2021), The Mother (2020)"
User: "Nội dung phim đầu tiên"
→ Trả lời: "The Father (2021) - [MÔ TẢ TỪ LỊCH SỬ]"

Lịch sử: "Phim Avatar rating 8.5/10, đạo diễn James Cameron"
User: "Đạo diễn là ai"
→ Trả lời: "Đạo diễn Avatar là James Cameron"

QUAN TRỌNG: Trích xuất CHÍNH XÁC, KHÔNG tự bịa."""
        
        self.context_model = gemini_service.create_model(self.context_instruction)
    
    async def process(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Xử lý câu hỏi dựa trên context"""
        
        # Lấy 10 tin nhắn gần nhất
        recent_history = state.history[-10:] if len(state.history) > 10 else state.history
        
        if not recent_history:
            return {
                "response": "Chưa có lịch sử chat. Hãy hỏi tôi về phim trước nhé! 😊",
                "agent": self.name,
                "metadata": {"context_available": False}
            }
        
        # TRY AI FIRST
        try:
            context = self._build_gemini_context(recent_history)
            
            # SIMPLIFIED PROMPT
            prompt = f"""Câu hỏi: "{message}"

Tìm và trích xuất thông tin từ lịch sử chat.
Nếu không có → "Tôi chưa đề cập thông tin đó trong cuộc trò chuyện."""
            
            chat = self.context_model.start_chat(history=context)
            
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    response = chat.send_message(prompt)
                    
                    if response and response.text and len(response.text) > 10:
                        return {
                            "response": response.text,
                            "agent": self.name,
                            "metadata": {"context_available": True, "method": "ai"}
                        }
                    else:
                        break  # Fallback to rule-based
                        
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        break  # Fallback
                        
        except Exception as e:
            print(f"[ContextAgent] AI failed: {e}, using rule-based")
        
        # FALLBACK: RULE-BASED EXTRACTION
        return self._rule_based_extraction(message, recent_history)
    
    def _rule_based_extraction(self, message: str, history: list) -> Dict[str, Any]:
        """FALLBACK: Extract info using rules"""
        
        message_lower = message.lower()
        
        # Find last assistant message with movie info
        last_movie_response = None
        for msg in reversed(history):
            if msg.get("role") == "assistant" and "🎬" in msg.get("content", ""):
                last_movie_response = msg.get("content", "")
                break
        
        if not last_movie_response:
            return {
                "response": "Tôi chưa đề cập phim nào trong cuộc trò chuyện này. Hãy hỏi tôi gợi ý phim trước nhé!",
                "agent": self.name,
                "metadata": {"method": "rule_based", "no_movie_found": True}
            }
        
        # EXTRACT ALL MOVIES from response
        all_movies = self._extract_all_movies(last_movie_response)
        
        if not all_movies:
            return {
                "response": "Không tìm thấy thông tin phim trong lịch sử chat.",
                "agent": self.name,
                "metadata": {"method": "rule_based", "no_movies_extracted": True}
            }
        
        # CHECK REQUEST TYPE
        # Request for N movies (e.g., "cho tôi 5 phim", "3 phim đầu")
        num_request = self._extract_number_request(message_lower)
        
        if num_request:
            num_to_show = min(num_request, len(all_movies))
            response_text = f"Dưới đây là {num_to_show} phim từ danh sách vừa rồi:\n\n"
            
            for i, movie in enumerate(all_movies[:num_to_show], 1):
                response_text += f"{i}. 🎬 **{movie['title']}** ({movie['year']})\n"
                response_text += f"   ⭐ {movie['rating']}\n"
                response_text += f"   🎭 {movie['genre']}\n"
                if movie['overview']:
                    response_text += f"   📝 {movie['overview'][:150]}...\n"
                response_text += "\n"
            
            return {
                "response": response_text,
                "agent": self.name,
                "metadata": {"method": "rule_based", "type": "list", "count": num_to_show}
            }
        
        # Single movie reference (first, second, etc.)
        movie_index = self._extract_movie_index(message_lower)
        
        if movie_index is not None and 0 <= movie_index < len(all_movies):
            movie = all_movies[movie_index]
            
            # Check what info is requested
            if any(word in message_lower for word in ["nội dung", "về gì", "kể về", "câu chuyện"]):
                return {
                    "response": f"""📝 **{movie['title']}** ({movie['year']})

{movie['overview'] or 'Chưa có thông tin chi tiết về nội dung phim này.'}

⭐ Rating: {movie['rating']}
🎭 Thể loại: {movie['genre']}
🎬 Đạo diễn: {movie['director']}""",
                    "agent": self.name,
                    "metadata": {"method": "rule_based", "type": "overview"}
                }
            
            elif any(word in message_lower for word in ["đạo diễn", "director"]):
                return {
                    "response": f"Đạo diễn phim **{movie['title']}** là: {movie['director']}",
                    "agent": self.name,
                    "metadata": {"method": "rule_based", "type": "director"}
                }
            
            else:
                # General info
                return {
                    "response": f"""📊 **{movie['title']}** ({movie['year']}):

⭐ Rating: {movie['rating']}
🎭 Thể loại: {movie['genre']}
🎬 Đạo diễn: {movie['director']}

📝 {movie['overview'][:300] if movie['overview'] else 'Chưa có mô tả.'}...""",
                    "agent": self.name,
                    "metadata": {"method": "rule_based", "type": "info"}
                }
        
        # DEFAULT: Return summary
        first_movie = all_movies[0]
        return {
            "response": f"""📊 Phim gần nhất tôi đề cập: **{first_movie['title']}** ({first_movie['year']})

⭐ Rating: {first_movie['rating']}
🎭 Thể loại: {first_movie['genre']}
🎬 Đạo diễn: {first_movie['director']}

Bạn muốn biết thêm gì? (Ví dụ: "nội dung phim", "cho tôi 5 phim")""",
            "agent": self.name,
            "metadata": {"method": "rule_based", "type": "default"}
        }
    
    def _extract_all_movies(self, text: str) -> list:
        """Extract all movies from response text"""
        movies = []
        
        # Pattern: **Title** (Year)
        pattern = r'\*\*(.+?)\*\*\s*\((\d{4})\)'
        matches = re.finditer(pattern, text)
        
        for match in matches:
            title = match.group(1)
            year = match.group(2)
            
            # Find corresponding info
            # Extract rating after this movie
            rating_pattern = rf'\*\*{re.escape(title)}\*\*.*?Rating:\s*([\d.]+)/10'
            rating_match = re.search(rating_pattern, text, re.DOTALL)
            rating = rating_match.group(1) if rating_match else "N/A"
            
            # Extract genre
            genre_pattern = rf'\*\*{re.escape(title)}\*\*.*?Thể loại:\s*([^\n]+)'
            genre_match = re.search(genre_pattern, text, re.DOTALL)
            genre = genre_match.group(1).strip() if genre_match else "N/A"
            
            # Extract director
            director_pattern = rf'\*\*{re.escape(title)}\*\*.*?Đạo diễn:\s*([^\n]+)'
            director_match = re.search(director_pattern, text, re.DOTALL)
            director = director_match.group(1).strip() if director_match else "N/A"
            
            # Extract overview
            overview_pattern = rf'\*\*{re.escape(title)}\*\*.*?📝\s*([^\n]+(?:\n(?!🎬|\*\*|Nguồn)[^\n]+)*)'
            overview_match = re.search(overview_pattern, text, re.DOTALL)
            overview = overview_match.group(1).strip() if overview_match else ""
            
            movies.append({
                'title': title,
                'year': year,
                'rating': rating,
                'genre': genre,
                'director': director,
                'overview': overview
            })
        
        return movies
    
    def _extract_number_request(self, message: str) -> int:
        """Extract number of movies requested (e.g., '5 phim', 'cho tôi 3')"""
        
        # Patterns: "5 phim", "cho tôi 3", "3 cái", etc.
        patterns = [
            r'(\d+)\s*phim',
            r'cho\s*(?:tôi|mình)\s*(\d+)',
            r'(\d+)\s*cái',
            r'(\d+)\s*bộ'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                try:
                    return int(match.group(1))
                except:
                    pass
        
        return None
    
    def _extract_movie_index(self, message: str) -> int:
        """Extract movie index from message (first=0, second=1, etc.)"""
        
        # Ordinal numbers
        ordinals = {
            "đầu": 0, "first": 0, "1": 0, "thứ nhất": 0,
            "thứ hai": 1, "second": 1, "2": 1,
            "thứ ba": 2, "third": 2, "3": 2,
            "thứ tư": 3, "fourth": 3, "4": 3,
            "thứ năm": 4, "fifth": 4, "5": 4
        }
        
        for key, index in ordinals.items():
            if key in message:
                return index
        
        return None
    
    async def can_handle(self, message: str, state: AgentState) -> bool:
        """Check if message is context-dependent"""
        
        # Không có history → không handle
        if not state.history or len(state.history) == 0:
            return False
        
        context_keywords = [
            # Direct references
            "vừa", "trước", "đó", "đây", "bạn nói", "bạn đề xuất",
            # List references
            "danh sách", "phim đầu", "phim thứ", "cái đầu", "cái thứ",
            # Number requests
            "cho tôi", "đưa tôi", "liệt kê",
            # Info requests WITHOUT new search
            "nội dung của", "thông tin về", "chi tiết", "đạo diễn", "rating",
            # Position references
            "trong đó", "ở trên", "phía trên", "như trên"
        ]
        
        message_lower = message.lower()
        
        # Must have context keyword
        has_keyword = any(keyword in message_lower for keyword in context_keywords)
        
        # KHÔNG handle nếu có từ TÌM KIẾM MỚI
        new_search_keywords = ["tìm", "gợi ý mới", "phim khác"]
        has_new_search = any(keyword in message_lower for keyword in new_search_keywords)
        
        # SPECIAL: "cho tôi N phim" without specific genre/search term
        # Should be context-based if recently talked about movies
        if re.search(r'cho\s*(?:tôi|mình)\s*\d+\s*phim', message_lower):
            # Check if recent history has movies
            for msg in reversed(state.history[-3:]):
                if msg.get("role") == "assistant" and "🎬" in msg.get("content", ""):
                    return True  # Handle as context
        
        return has_keyword and not has_new_search
    
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