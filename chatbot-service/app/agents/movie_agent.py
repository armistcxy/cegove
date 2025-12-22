# app/agents/movie_agent.py
from app.agents.base import BaseAgent
from app.models.agent_state import AgentState
from app.services.gemini_service import gemini_service
from app.services.api_client import api_client
from app.services.knowledge_service import knowledge_service
from typing import Dict, Any, List
import json
import time

class MovieAgent(BaseAgent):
    """Movie Agent - Chuyên về thông tin phim"""
    
    def __init__(self):
        super().__init__("movie")
        
        # System instruction cho extraction - CÓ GENRE MAPPING
        self.extraction_instruction = f"""Bạn là trợ lý trích xuất thông tin tìm kiếm phim.

{knowledge_service.get_genre_mapping_text()}

Quan trọng:
- Nếu user nói tiếng Việt, PHẢI chuyển sang tiếng Anh
- Ví dụ: "phim hành động" → genre: "Action"
- Ví dụ: "phim hoạt hình" → genre: "Animation"

Chỉ trả về JSON hợp lệ."""
        
        # System instruction cho response generation - CÓ SYSTEM KNOWLEDGE
        self.response_instruction = f"""Bạn là chuyên gia tư vấn phim ảnh thân thiện và am hiểu.

{knowledge_service.get_system_knowledge()}

Nhiệm vụ:
- Giúp người dùng tìm phim phù hợp với sở thích
- Gợi ý phim hay dựa trên thông tin có sẵn
- Giải thích về nội dung, diễn viên, đạo diễn
- Đưa ra đánh giá và nhận xét về phim

Khi trả lời:
- Sử dụng thông tin được cung cấp từ database
- Trả lời ngắn gọn, súc tích nhưng đầy đủ thông tin
- Highlight những điểm đặc biệt, thú vị của phim
- Nếu có nhiều phim phù hợp, liệt kê 3-5 phim tốt nhất
- Luôn kèm theo thông tin: tên phim, năm, rating, thể loại
- Nếu user hỏi về hệ thống, dựa vào knowledge để trả lời

Format trả lời:
🎬 **Tên Phim** (Năm) - ⭐ Rating
📝 Mô tả ngắn gọn
🎭 Thể loại | 🎬 Đạo diễn | ⏱️ Thời lượng

Trả lời bằng tiếng Việt, nhiệt tình và hữu ích."""
        
        # Khởi tạo models một lần
        self.extraction_model = gemini_service.create_model(self.extraction_instruction)
        self.response_model = gemini_service.create_model(self.response_instruction)
    
    async def process(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Xử lý yêu cầu về phim"""
        
        # Extract search parameters from message using Gemini
        params = await self._extract_search_params(message)
        
        # Translate Vietnamese genre to English if needed
        if params.get("genre"):
            translated = knowledge_service.translate_genre_vi_to_en(params["genre"])
            if translated:
                print(f"[MovieAgent] Translated genre: {params['genre']} → {translated}")
                params["genre"] = translated
        
        # Search movies based on parameters
        movies_data = await self._search_movies(params)
        
        # Generate response with movie data
        response = await self._generate_movie_response(
            message=message,
            movies_data=movies_data,
            state=state
        )
        
        return {
            "response": response,
            "agent": self.name,
            "metadata": {
                "movies_count": len(movies_data.get("movies", [])),
                "search_params": params
            }
        }
    
    async def can_handle(self, message: str, state: AgentState) -> bool:
        """Check if this agent can handle the message"""
        keywords = ["phim", "movie", "xem", "gợi ý", "tìm", "thể loại", "diễn viên", "đạo diễn"]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in keywords)
    
    async def _extract_search_params(self, message: str) -> Dict[str, Any]:
        """Extract search parameters from message - Dùng model đã khởi tạo"""
        
        extraction_prompt = f"""Phân tích yêu cầu và trích xuất thông tin tìm kiếm phim:

Tin nhắn: "{message}"

Trích xuất các thông tin (nếu có):
- query: Từ khóa tìm kiếm chung (tên phim)
- genre: Thể loại phim (PHẢI BẰNG TIẾNG ANH - dùng mapping ở trên)
- year: Năm phát hành
- min_rating: Rating tối thiểu (0-10)
- sort_by: Sắp xếp theo (rating, released_year, meta_score)

Trả về JSON:
{{
    "query": "...",
    "genre": "Action",  // CHÚ Ý: Phải tiếng Anh
    "year": "...",
    "min_rating": 7.0,
    "sort_by": "rating"
}}

Chỉ trả về các field có thông tin, bỏ qua field không xác định được."""
        
        try:
            # Retry logic
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    response = self.extraction_model.generate_content(extraction_prompt)
                    
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
                    return result if isinstance(result, dict) else {}
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        raise
        except Exception as e:
            print(f"Error extracting params: {e}")
            # Fallback: simple keyword extraction
            return {"query": message}
    
    async def _search_movies(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search movies using API"""
        
        # If has specific query, use search endpoint
        if params.get("query"):
            movies = await api_client.search_movies(
                query=params["query"],
                limit=10
            )
            return {"movies": movies, "total": len(movies)}
        
        # Otherwise use filter endpoint
        movies_response = await api_client.get_movies(
            page=1,
            page_size=10,
            genre=params.get("genre"),
            year=params.get("year"),
            min_rating=params.get("min_rating"),
            sort_by=params.get("sort_by", "rating")
        )
        
        return {
            "movies": movies_response.get("items", []),
            "total": movies_response.get("total", 0)
        }
    
    async def _generate_movie_response(
        self,
        message: str,
        movies_data: Dict[str, Any],
        state: AgentState
    ) -> str:
        """Generate response with movie information - Dùng model đã khởi tạo"""
        
        movies = movies_data.get("movies", [])
        total_found = movies_data.get("total", len(movies))
        
        if not movies:
            return """Xin lỗi, tôi không tìm thấy phim nào phù hợp trong database. 😔

Bạn có thể thử:
- Tìm với từ khóa khác
- Mở rộng tiêu chí (bỏ năm, rating...)
- Hỏi tôi "có những phim nào" để xem danh sách

Tôi chỉ tìm trong database CÓ SẴN nhé!"""
        
        # Format movie data for Gemini
        movies_info = self._format_movies_info(movies[:5])  # Top 5
        
        # Build context from history
        context = self._build_gemini_context(state.history[-6:] if len(state.history) > 0 else [])
        
        prompt = f"""Người dùng hỏi: "{message}"

DATABASE TRẢ VỀ {total_found} phim. Dưới đây là top {len(movies[:5])} phim:

{movies_info}

NHIỆM VỤ:
1. Phân tích CHÍNH XÁC {len(movies[:5])} phim trên
2. Gợi ý 3-5 phim TỐT NHẤT từ danh sách
3. Giải thích dựa trên dữ liệu CÓ (rating, thể loại, đạo diễn)
4. KHÔNG đề cập phim không có trong danh sách

BẮT BUỘC:
- Bắt đầu: "Tôi tìm thấy {total_found} phim trong database..."
- Chỉ nói về các phim ĐƯỢC LIET KÊ ở trên
- Dùng đúng tên, năm, rating từ database
- Nếu user hỏi về phim không có → "Phim đó không có trong danh sách tìm được"

Trả lời ngắn gọn, chính xác, dựa 100% vào dữ liệu trên."""
        
        try:
            # Sử dụng model đã khởi tạo sẵn
            chat = self.response_model.start_chat(history=context)
            
            # Retry logic
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    response = chat.send_message(prompt)
                    return response.text
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        raise
        except Exception as e:
            print(f"Error generating movie response: {e}")
            if "429" in str(e):
                # Fallback: simple response với dữ liệu thật
                movie = movies[0]
                return f"""📊 Database tìm thấy {total_found} phim. Gợi ý top 1:

🎬 **{movie.get('series_title')}** ({movie.get('released_year')})
⭐ Rating: {movie.get('imdb_rating')}/10
🎭 Thể loại: {movie.get('genre')}
🎬 Đạo diễn: {movie.get('director')}

📝 {movie.get('overview', 'Một bộ phim hay trong hệ thống!')}

Nguồn: Database hệ thống"""
            return "Xin lỗi, tôi gặp sự cố khi phân tích. Vui lòng thử lại."
    
    def _format_movies_info(self, movies: List[Dict[str, Any]]) -> str:
        """Format movies into readable text"""
        formatted = []
        
        for movie in movies:
            # Safely get overview with proper None handling
            overview = movie.get('overview') or 'N/A'
            overview_text = overview[:200] if overview != 'N/A' else 'N/A'
            
            # Safely get stars list
            stars = movie.get('stars', [])
            stars_text = ', '.join(stars[:3]) if stars else 'N/A'
            
            info = f"""
- **{movie.get('series_title', 'N/A')}** ({movie.get('released_year', 'N/A')})
  Rating: {movie.get('imdb_rating', 'N/A')}/10 | Meta Score: {movie.get('meta_score', 'N/A')}
  Thể loại: {movie.get('genre', 'N/A')}
  Đạo diễn: {movie.get('director', 'N/A')}
  Diễn viên: {stars_text}
  Mô tả: {overview_text}...
  Runtime: {movie.get('runtime', 'N/A')} phút
"""
            formatted.append(info)
        
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
