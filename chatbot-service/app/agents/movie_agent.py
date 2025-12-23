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
        
        # System instruction cho extraction - ĐƠN GIẢN HÓA
        self.extraction_instruction = f"""Bạn là trợ lý trích xuất thông tin tìm kiếm phim.

{knowledge_service.get_genre_mapping_text()}

NHIỆM VỤ: Trích xuất thông tin TÌM KIẾM từ câu hỏi user.

QUY TẮC:
1. Nếu user NÓI TÊN PHIM cụ thể → dùng "query"
2. Nếu user chỉ nói THỂ LOẠI → dùng "genre" (tiếng Anh)
3. Ưu tiên "query" hơn "genre" khi không chắc

Ví dụ:
- "phim batman" → {{"query": "batman"}}
- "phim hoạt hình" → {{"genre": "Animation"}}
- "phim hành động hay" → {{"genre": "Action", "min_rating": 7.0}}

CHỈ trả JSON, KHÔNG giải thích."""
        
        # Response instruction giữ nguyên
        self.response_instruction = f"""Bạn là chuyên gia tư vấn phim ảnh thân thiện và am hiểu.

{knowledge_service.get_system_knowledge()}

NGUYÊN TẮC:
- CHỈ dùng thông tin từ DATABASE được cung cấp
- KHÔNG tự bịa phim
- Nếu không có phim → nói thật

Format:
🎬 **Tên Phim** (Năm) - ⭐ Rating
📝 Mô tả
🎭 Thể loại | 🎬 Đạo diễn

Trả lời bằng tiếng Việt."""
        
        # Khởi tạo models
        self.extraction_model = gemini_service.create_model(self.extraction_instruction)
        self.response_model = gemini_service.create_model(self.response_instruction)
    
    async def process(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Xử lý yêu cầu về phim"""
        
        # Extract search parameters - CẢI THIỆN
        params = await self._extract_search_params(message)
        
        # LOG RA ĐỂ DEBUG
        print(f"[MovieAgent] Extracted params: {params}")
        
        # Translate Vietnamese genre to English if needed
        if params.get("genre"):
            translated = knowledge_service.translate_genre_vi_to_en(params["genre"])
            if translated:
                print(f"[MovieAgent] Translated genre: {params['genre']} → {translated}")
                params["genre"] = translated
        
        # Search movies - CẢI THIỆN
        movies_data = await self._search_movies(params, message)
        
        # LOG KẾT QUẢ
        print(f"[MovieAgent] Found {len(movies_data.get('movies', []))} movies")
        
        # Generate response
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
        """Extract search parameters - CẢI THIỆN VỚI FALLBACK"""
        
        # Đơn giản hóa prompt
        extraction_prompt = f"""Tin nhắn: "{message}"

Trích xuất thông tin tìm kiếm:
- query: Tên phim (nếu user nói cụ thể)
- genre: Thể loại (BẰNG TIẾNG ANH, dùng mapping)
- min_rating: Rating tối thiểu (nếu user yêu cầu phim "hay", "tốt")

Trả về JSON ngắn gọn:
{{"query": "..."}} HOẶC {{"genre": "Action"}} HOẶC {{"query": "...", "min_rating": 7.0}}

CHỈ JSON, không text khác."""
        
        try:
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    response = self.extraction_model.generate_content(extraction_prompt)
                    text = response.text.strip()
                    
                    # Clean JSON
                    if text.startswith("```json"):
                        text = text[7:]
                    if text.startswith("```"):
                        text = text[3:]
                    if text.endswith("```"):
                        text = text[:-3]
                    text = text.strip()
                    
                    result = json.loads(text)
                    
                    # Validate result
                    if isinstance(result, dict) and (result.get("query") or result.get("genre")):
                        return result
                    else:
                        # Fallback to simple extraction
                        return self._simple_extraction(message)
                        
                except json.JSONDecodeError as e:
                    print(f"[MovieAgent] JSON parse error: {e}, text: {text}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                    else:
                        return self._simple_extraction(message)
                        
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        print(f"[MovieAgent] Extraction error: {e}")
                        return self._simple_extraction(message)
                        
        except Exception as e:
            print(f"[MovieAgent] Fatal extraction error: {e}")
            return self._simple_extraction(message)
    
    def _simple_extraction(self, message: str) -> Dict[str, Any]:
        """FALLBACK: Rule-based extraction khi AI thất bại"""
        message_lower = message.lower()
        params = {}
        
        print(f"[MovieAgent] Using simple extraction for: {message}")
        
        # Detect genre keywords (Vietnamese)
        genre_map = {
            "hoạt hình": "Animation",
            "hành động": "Action",
            "phiêu lưu": "Adventure",
            "hài": "Comedy",
            "tâm lý": "Drama",
            "kinh dị": "Horror",
            "khoa học viễn tưởng": "Sci-Fi",
            "tình cảm": "Romance",
            "tội phạm": "Crime",
            "chiến tranh": "War",
            "lịch sử": "History"
        }
        
        # Check for genre
        for vn_genre, en_genre in genre_map.items():
            if vn_genre in message_lower:
                params["genre"] = en_genre
                print(f"[MovieAgent] Detected genre: {vn_genre} → {en_genre}")
                break
        
        # If no genre, treat entire message as query
        if not params.get("genre"):
            # Remove common words
            query = message_lower.replace("phim", "").replace("xem", "").replace("tìm", "").replace("gợi ý", "").strip()
            if query:
                params["query"] = query
                print(f"[MovieAgent] Using query: {query}")
        
        # Check for quality keywords
        if any(word in message_lower for word in ["hay", "tốt", "đỉnh", "nổi tiếng"]):
            params["min_rating"] = 7.0
            print(f"[MovieAgent] Added min_rating: 7.0")
        
        return params if params else {"query": message}
    
    async def _search_movies(self, params: Dict[str, Any], original_message: str) -> Dict[str, Any]:
        """Search movies - CẢI THIỆN VỚI BETTER SEARCH LOGIC"""
        
        print(f"[MovieAgent] Searching with params: {params}")
        
        # Strategy 1: Search by query (EXACT MATCH PRIORITY)
        if params.get("query"):
            query = params["query"].strip()
            
            # Try exact match first
            movies = await api_client.search_movies(query=query, limit=10)
            
            if movies:
                print(f"[MovieAgent] Strategy 1 (query='{query}') found {len(movies)} movies")
                
                # FILTER: Ensure query appears in title
                filtered_movies = []
                query_lower = query.lower()
                
                for movie in movies:
                    title = movie.get('series_title', '').lower()
                    if query_lower in title:
                        filtered_movies.append(movie)
                
                # If filtered results exist, use them; otherwise use all
                if filtered_movies:
                    print(f"[MovieAgent] Filtered to {len(filtered_movies)} movies matching '{query}'")
                    return {"movies": filtered_movies, "total": len(filtered_movies)}
                else:
                    print(f"[MovieAgent] No exact matches, using all {len(movies)} results")
                    return {"movies": movies, "total": len(movies)}
            else:
                print(f"[MovieAgent] Strategy 1 (query) found 0 movies")
        
        # Strategy 2: Filter by genre/rating
        if params.get("genre") or params.get("min_rating"):
            movies_response = await api_client.get_movies(
                page=1,
                page_size=10,
                genre=params.get("genre"),
                year=params.get("year"),
                min_rating=params.get("min_rating"),
                sort_by="rating"
            )
            
            movies = movies_response.get("items", [])
            if movies:
                print(f"[MovieAgent] Strategy 2 (filter) found {len(movies)} movies")
                return {
                    "movies": movies,
                    "total": movies_response.get("total", len(movies))
                }
            else:
                print(f"[MovieAgent] Strategy 2 (filter) found 0 movies")
        
        # Strategy 3: Fallback - KHÔNG LẤY TẤT CẢ, BÁO LỖI
        print(f"[MovieAgent] No results found, returning empty")
        return {"movies": [], "total": 0}
    
    async def _generate_movie_response(
        self,
        message: str,
        movies_data: Dict[str, Any],
        state: AgentState
    ) -> str:
        """Generate response - GIỐNG NHƯ CŨ"""
        
        movies = movies_data.get("movies", [])
        total_found = movies_data.get("total", len(movies))
        
        if not movies:
            return """Xin lỗi, tôi không tìm thấy phim nào phù hợp trong database. 😔

Bạn có thể thử:
- Tìm với từ khóa khác (VD: "action", "comedy")
- Hỏi "có những phim nào" để xem danh sách
- Tìm theo tên cụ thể (VD: "phim Avatar")

Tôi chỉ tìm trong database CÓ SẴN nhé!"""
        
        # Format movie data for Gemini
        movies_info = self._format_movies_info(movies[:5])
        
        # Build context from history
        context = self._build_gemini_context(state.history[-6:] if len(state.history) > 0 else [])
        
        prompt = f"""User hỏi: "{message}"

DATABASE: Tìm thấy {total_found} phim. Top {len(movies[:5])}:

{movies_info}

NHIỆM VỤ:
- Gợi ý 3-5 phim TỐT NHẤT
- Dùng ĐÚNG thông tin từ database
- Giải thích ngắn gọn

Trả lời bằng tiếng Việt."""
        
        try:
            chat = self.response_model.start_chat(history=context)
            
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
            print(f"Error generating response: {e}")
            # Fallback: Simple response
            movie = movies[0]
            return f"""📊 Tìm thấy {total_found} phim trong database!

Top gợi ý:

🎬 **{movie.get('series_title')}** ({movie.get('released_year')})
⭐ Rating: {movie.get('imdb_rating')}/10
🎭 Thể loại: {movie.get('genre')}
🎬 Đạo diễn: {movie.get('director')}

📝 {movie.get('overview', 'Một bộ phim hay!')}

Nguồn: Database hệ thống"""
    
    def _format_movies_info(self, movies: List[Dict[str, Any]]) -> str:
        """Format movies - GIỐNG CŨ"""
        formatted = []
        
        for movie in movies:
            overview = movie.get('overview') or 'N/A'
            overview_text = overview[:200] if overview != 'N/A' else 'N/A'
            
            stars = movie.get('stars', [])
            stars_text = ', '.join(stars[:3]) if stars else 'N/A'
            
            info = f"""
- **{movie.get('series_title', 'N/A')}** ({movie.get('released_year', 'N/A')})
  Rating: {movie.get('imdb_rating', 'N/A')}/10 | Meta: {movie.get('meta_score', 'N/A')}
  Thể loại: {movie.get('genre', 'N/A')}
  Đạo diễn: {movie.get('director', 'N/A')}
  Diễn viên: {stars_text}
  Mô tả: {overview_text}...
  Runtime: {movie.get('runtime', 'N/A')} phút
"""
            formatted.append(info)
        
        return "\n".join(formatted)
    
    def _build_gemini_context(self, history: list) -> list:
        """Convert history - GIỐNG CŨ"""
        gemini_history = []
        for msg in history:
            role = "model" if msg["role"] == "assistant" else "user"
            gemini_history.append({
                "role": role,
                "parts": [msg["content"]]
            })
        return gemini_history
