# app/agents/context_agent.py
from app.agents.base import BaseAgent
from app.models.agent_state import AgentState
from app.services.gemini_service import gemini_service
from app.services.api_client import api_client
from typing import Dict, Any, List, Optional
import re
import time

class ContextAgent(BaseAgent):
    """
    Context Agent - Xử lý câu hỏi dựa trên ngữ cảnh
    
    Hỗ trợ Scenario 5: Truy vấn dựa trên lịch sử
    - "Phim thứ 2 bạn vừa kể nội dung gì?"
    - "Cho tôi 5 phim từ danh sách"
    - "Đạo diễn phim đầu tiên là ai?"
    """
    
    def __init__(self):
        super().__init__("context")
        
        self.context_instruction = """Bạn là trợ lý trích xuất thông tin từ lịch sử chat.

NHIỆM VỤ:
1. Đọc lịch sử chat để tìm thông tin user hỏi
2. Trích xuất CHÍNH XÁC - KHÔNG tự bịa
3. Trả lời ngắn gọn, đúng trọng tâm

EXAMPLES:
- Lịch sử có "The Dark Knight (2008), rating 9.0" → User hỏi "rating" → Trả lời "9.0/10"
- Lịch sử có 5 phim → User hỏi "phim thứ 3" → Trả về info phim thứ 3
- Không có thông tin → Trả lời "Tôi chưa đề cập thông tin đó"

QUAN TRỌNG: 
- CHỈ dùng thông tin CÓ TRONG lịch sử
- KHÔNG tự tạo thông tin mới"""
        
        self.context_model = gemini_service.create_model(self.context_instruction)
    
    async def process(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Xử lý câu hỏi context-based - Scenario 5"""
        
        recent_history = state.history[-10:] if len(state.history) > 10 else state.history
        
        if not recent_history:
            return {
                "response": "Chưa có lịch sử chat. Hãy hỏi tôi về phim trước nhé! 🎬",
                "agent": self.name,
                "metadata": {"context_available": False}
            }
        
        message_lower = message.lower()
        
        # === Check if asking for movie detail by ID from context ===
        movie_ref = self._extract_movie_reference(message_lower, state)
        if movie_ref:
            return await self._handle_movie_reference(movie_ref, message_lower, state)
        
        # === Check for list request (e.g., "cho tôi 5 phim") ===
        list_request = self._extract_list_request(message_lower)
        if list_request:
            return self._handle_list_request(list_request, recent_history)
        
        # === Try AI for complex context questions ===
        try:
            context = self._build_gemini_context(recent_history)
            
            prompt = f"""Câu hỏi: "{message}"

Tìm và trích xuất thông tin từ lịch sử chat.
Trả lời ngắn gọn, chính xác.
Nếu không có thông tin → "Tôi chưa đề cập điều đó trong cuộc trò chuyện này." """
            
            chat = self.context_model.start_chat(history=context)
            
            for attempt in range(2):
                try:
                    response = chat.send_message(prompt)
                    
                    if response and response.text and len(response.text) > 10:
                        return {
                            "response": response.text,
                            "agent": self.name,
                            "metadata": {"method": "ai", "context_available": True}
                        }
                    break
                except Exception as e:
                    if "429" in str(e) and attempt == 0:
                        time.sleep(2)
                    else:
                        break
        except Exception as e:
            print(f"[ContextAgent] AI failed: {e}")
        
        # === Fallback: Rule-based extraction ===
        return self._rule_based_extraction(message, recent_history)
    
    def _extract_movie_reference(self, message: str, state: AgentState) -> Optional[Dict]:
        """Extract movie reference (phim đầu, phim thứ 2, etc.)"""
        
        # Ordinal patterns
        ordinals = {
            "đầu tiên": 0, "đầu": 0, "first": 0, "thứ nhất": 0, "số 1": 0,
            "thứ hai": 1, "thứ 2": 1, "second": 1, "số 2": 1,
            "thứ ba": 2, "thứ 3": 2, "third": 2, "số 3": 2,
            "thứ tư": 3, "thứ 4": 3, "fourth": 3, "số 4": 3,
            "thứ năm": 4, "thứ 5": 4, "fifth": 4, "số 5": 4,
            "cuối": -1, "cuối cùng": -1, "last": -1
        }
        
        for key, index in ordinals.items():
            if key in message:
                # Get movie from context
                if state.movie_context and state.movie_context.movie_ids:
                    movie_ids = state.movie_context.movie_ids
                    movie_titles = state.movie_context.movie_titles
                    
                    if index == -1:
                        index = len(movie_ids) - 1
                    
                    if 0 <= index < len(movie_ids):
                        return {
                            "index": index,
                            "movie_id": movie_ids[index],
                            "movie_title": movie_titles[index] if index < len(movie_titles) else None
                        }
        
        return None
    
    async def _handle_movie_reference(self, movie_ref: Dict, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle question about specific movie from context"""
        
        movie_id = movie_ref.get("movie_id")
        movie_title = movie_ref.get("movie_title", "Phim")
        index = movie_ref.get("index", 0)
        
        # Determine what info is requested
        info_type = self._determine_info_type(message)
        
        # Get movie detail from API
        if movie_id:
            try:
                movie_detail = await api_client.get_movie_detail(int(movie_id))
                
                if movie_detail:
                    return self._format_movie_info(movie_detail, info_type, index + 1)
            except Exception as e:
                print(f"[ContextAgent] Error getting movie detail: {e}")
        
        # Fallback: use info from history
        return self._extract_from_history(movie_title, info_type, state.history)
    
    def _determine_info_type(self, message: str) -> str:
        """Determine what type of info user is asking for"""
        
        if any(w in message for w in ["nội dung", "về gì", "kể về", "tóm tắt", "overview"]):
            return "overview"
        elif any(w in message for w in ["đạo diễn", "director", "ai đạo diễn"]):
            return "director"
        elif any(w in message for w in ["diễn viên", "actor", "cast", "đóng"]):
            return "cast"
        elif any(w in message for w in ["rating", "điểm", "đánh giá", "imdb"]):
            return "rating"
        elif any(w in message for w in ["thể loại", "genre", "loại phim"]):
            return "genre"
        elif any(w in message for w in ["năm", "year", "ra mắt", "phát hành"]):
            return "year"
        elif any(w in message for w in ["thời lượng", "dài bao lâu", "runtime", "bao lâu"]):
            return "runtime"
        
        return "full"  # Return all info
    
    def _format_movie_info(self, movie: Dict, info_type: str, position: int) -> Dict[str, Any]:
        """Format movie info based on requested type"""
        
        title = movie.get("series_title", "N/A")
        year = movie.get("released_year", "N/A")
        
        if info_type == "overview":
            overview = movie.get("overview", "Chưa có thông tin mô tả.")
            response = f"""📝 **{title}** ({year}):

{overview}"""
        
        elif info_type == "director":
            director = movie.get("director", "Chưa có thông tin")
            response = f"🎬 Đạo diễn phim **{title}**: {director}"
        
        elif info_type == "cast":
            stars = movie.get("stars", [])
            if isinstance(stars, list):
                cast_text = ", ".join(stars[:4]) if stars else "Chưa có thông tin"
            else:
                cast_text = str(stars)
            response = f"🌟 Diễn viên phim **{title}**: {cast_text}"
        
        elif info_type == "rating":
            rating = movie.get("imdb_rating", "N/A")
            meta = movie.get("meta_score", "N/A")
            response = f"⭐ Rating phim **{title}**: {rating}/10 (IMDB) | Meta: {meta}"
        
        elif info_type == "genre":
            genre = movie.get("genre", "N/A")
            response = f"🎭 Thể loại phim **{title}**: {genre}"
        
        elif info_type == "year":
            response = f"📅 Phim **{title}** ra mắt năm: {year}"
        
        elif info_type == "runtime":
            runtime = movie.get("runtime", "N/A")
            response = f"⏱️ Thời lượng phim **{title}**: {runtime}"
        
        else:  # full info
            response = f"""📊 **{title}** ({year}) - Phim #{position}

⭐ Rating: {movie.get('imdb_rating', 'N/A')}/10
🎭 Thể loại: {movie.get('genre', 'N/A')}
🎬 Đạo diễn: {movie.get('director', 'N/A')}
⏱️ Thời lượng: {movie.get('runtime', 'N/A')}

📝 {movie.get('overview', 'Chưa có mô tả.')[:300]}..."""
        
        return {
            "response": response,
            "agent": self.name,
            "metadata": {"method": "api", "info_type": info_type, "movie_id": movie.get("id")}
        }
    
    def _extract_list_request(self, message: str) -> Optional[int]:
        """Extract number of items requested"""
        
        patterns = [
            r'(\d+)\s*phim',
            r'cho\s*(?:tôi|mình)\s*(\d+)',
            r'(\d+)\s*(?:cái|bộ|phim)',
            r'top\s*(\d+)',
            r'(\d+)\s*đầu'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return min(int(match.group(1)), 10)  # Max 10
        
        return None
    
    def _handle_list_request(self, count: int, history: list) -> Dict[str, Any]:
        """Handle request for N movies from history"""
        
        # Extract movies from recent assistant messages
        all_movies = []
        
        for msg in reversed(history):
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                movies = self._extract_movies_from_text(content)
                all_movies.extend(movies)
                
                if len(all_movies) >= count:
                    break
        
        if not all_movies:
            return {
                "response": "Tôi chưa đề cập phim nào trong cuộc trò chuyện này. Hãy hỏi 'Gợi ý phim hay' để tôi tìm cho bạn!",
                "agent": self.name,
                "metadata": {"no_movies": True}
            }
        
        # Format response
        num_to_show = min(count, len(all_movies))
        response_text = f"📋 **{num_to_show} phim từ danh sách vừa rồi:**\n\n"
        
        for i, movie in enumerate(all_movies[:num_to_show], 1):
            response_text += f"{i}. 🎬 **{movie['title']}** ({movie.get('year', 'N/A')})\n"
            if movie.get('rating'):
                response_text += f"   ⭐ Rating: {movie['rating']}\n"
            if movie.get('genre'):
                response_text += f"   🎭 {movie['genre']}\n"
            response_text += "\n"
        
        response_text += "💡 Muốn biết chi tiết phim nào? Hỏi 'Nội dung phim thứ 1' nhé!"
        
        return {
            "response": response_text,
            "agent": self.name,
            "metadata": {"method": "list_extraction", "count": num_to_show}
        }
    
    def _extract_movies_from_text(self, text: str) -> List[Dict]:
        """Extract movie info from text"""
        movies = []
        
        # Pattern 1: **Title** (Year)
        pattern1 = r'\*\*(.+?)\*\*\s*\((\d{4})\)'
        
        for match in re.finditer(pattern1, text):
            title = match.group(1)
            year = match.group(2)
            
            movie_data = {'title': title, 'year': year}
            
            # Try to extract more info after this match
            remaining_text = text[match.end():match.end()+500]
            
            # Rating
            rating_match = re.search(r'Rating:\s*([\d.]+)', remaining_text)
            if rating_match:
                movie_data['rating'] = rating_match.group(1)
            
            # Genre
            genre_match = re.search(r'Thể loại:\s*([^\n]+)', remaining_text)
            if genre_match:
                movie_data['genre'] = genre_match.group(1).strip()
            
            # Director
            director_match = re.search(r'Đạo diễn:\s*([^\n]+)', remaining_text)
            if director_match:
                movie_data['director'] = director_match.group(1).strip()
            
            # Overview
            overview_match = re.search(r'📝\s*([^\n]+)', remaining_text)
            if overview_match:
                movie_data['overview'] = overview_match.group(1).strip()
            
            movies.append(movie_data)
        
        return movies
    
    def _extract_from_history(self, movie_title: str, info_type: str, history: list) -> Dict[str, Any]:
        """Fallback: Extract info from history when API fails"""
        
        for msg in reversed(history):
            if msg.get("role") == "assistant" and movie_title.lower() in msg.get("content", "").lower():
                content = msg.get("content", "")
                
                # Try to extract requested info
                if info_type == "director":
                    match = re.search(r'Đạo diễn:\s*([^\n]+)', content)
                    if match:
                        return {
                            "response": f"🎬 Đạo diễn phim **{movie_title}**: {match.group(1).strip()}",
                            "agent": self.name,
                            "metadata": {"method": "history_extraction"}
                        }
                
                elif info_type == "rating":
                    match = re.search(r'Rating:\s*([\d.]+)', content)
                    if match:
                        return {
                            "response": f"⭐ Rating phim **{movie_title}**: {match.group(1)}/10",
                            "agent": self.name,
                            "metadata": {"method": "history_extraction"}
                        }
                
                # Return full movie info found in history
                movies = self._extract_movies_from_text(content)
                for m in movies:
                    if m['title'].lower() == movie_title.lower():
                        return {
                            "response": f"""📊 **{m['title']}** ({m.get('year', 'N/A')}):

⭐ Rating: {m.get('rating', 'N/A')}/10
🎭 Thể loại: {m.get('genre', 'N/A')}
🎬 Đạo diễn: {m.get('director', 'N/A')}""",
                            "agent": self.name,
                            "metadata": {"method": "history_extraction"}
                        }
        
        return {
            "response": f"Không tìm thấy thông tin chi tiết về phim '{movie_title}' trong lịch sử chat.",
            "agent": self.name,
            "metadata": {"not_found": True}
        }
    
    def _rule_based_extraction(self, message: str, history: list) -> Dict[str, Any]:
        """Fallback rule-based extraction"""
        
        message_lower = message.lower()
        
        # Find last assistant message with movie info
        last_movie_response = None
        for msg in reversed(history):
            if msg.get("role") == "assistant" and "🎬" in msg.get("content", ""):
                last_movie_response = msg.get("content", "")
                break
        
        if not last_movie_response:
            return {
                "response": "Tôi chưa đề cập phim nào trong cuộc trò chuyện này. Hãy hỏi tôi gợi ý phim trước nhé! 🎬",
                "agent": self.name,
                "metadata": {"no_movies": True}
            }
        
        # Extract movies
        movies = self._extract_movies_from_text(last_movie_response)
        
        if not movies:
            return {
                "response": "Không tìm thấy thông tin phim trong lịch sử. Hãy thử hỏi cụ thể hơn!",
                "agent": self.name,
                "metadata": {"extraction_failed": True}
            }
        
        # Default: return first movie info
        movie = movies[0]
        return {
            "response": f"""📊 Phim gần nhất tôi đề cập: **{movie['title']}** ({movie.get('year', 'N/A')})

⭐ Rating: {movie.get('rating', 'N/A')}/10
🎭 Thể loại: {movie.get('genre', 'N/A')}
🎬 Đạo diễn: {movie.get('director', 'N/A')}

Bạn muốn biết thêm gì? (VD: "nội dung phim", "cho tôi 5 phim")""",
            "agent": self.name,
            "metadata": {"method": "rule_based", "movies_found": len(movies)}
        }
    
    async def can_handle(self, message: str, state: AgentState) -> bool:
        """Check if message is context-dependent"""
        
        if not state.history:
            return False
        
        message_lower = message.lower()
        
        # Context keywords
        context_keywords = [
            # Direct references
            "vừa", "vừa rồi", "vừa nói", "trước đó", "ở trên", "bạn nói", "bạn đề xuất",
            # List/position references  
            "danh sách", "phim đầu", "phim thứ", "phim cuối", "cái đầu", "cái thứ",
            "số 1", "số 2", "số 3", "thứ nhất", "thứ hai", "thứ ba",
            # Number requests
            "cho tôi", "đưa tôi", "liệt kê", "top",
            # Info about previous context
            "nội dung của", "thông tin về", "chi tiết về",
            # Relative references
            "trong đó", "phía trên", "như trên", "ở đây"
        ]
        
        has_context_keyword = any(kw in message_lower for kw in context_keywords)
        
        # Skip if clearly new search
        new_search_keywords = ["tìm phim mới", "gợi ý mới", "phim khác", "tìm kiếm"]
        has_new_search = any(kw in message_lower for kw in new_search_keywords)
        
        if has_new_search:
            return False
        
        # Special: "cho tôi N phim" should be context-based
        if re.search(r'cho\s*(?:tôi|mình)\s*\d+\s*phim', message_lower):
            for msg in reversed(state.history[-3:]):
                if msg.get("role") == "assistant" and "🎬" in msg.get("content", ""):
                    return True
        
        return has_context_keyword
    
    def _build_gemini_context(self, history: list) -> list:
        """Convert history to Gemini format"""
        return [
            {
                "role": "model" if msg["role"] == "assistant" else "user",
                "parts": [msg["content"]]
            }
            for msg in history
        ]