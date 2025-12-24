# app/agents/movie_agent.py
from app.agents.base import BaseAgent
from app.models.agent_state import AgentState, MovieContext
from app.services.gemini_service import gemini_service
from app.services.api_client import api_client
from app.services.knowledge_service import knowledge_service
from typing import Dict, Any, List, Optional
import json
import time
import re

class MovieAgent(BaseAgent):
    """
    Movie Agent - Chuyên về thông tin phim
    Hỗ trợ: Scenario 1, 2, 3, 7
    """
    
    def __init__(self):
        super().__init__("movie")
        
        self.extraction_instruction = f"""Bạn là trợ lý trích xuất thông tin tìm kiếm phim.

{knowledge_service.get_genre_mapping_text()}

NHIỆM VỤ: Trích xuất TÊN PHIM hoặc THỂ LOẠI từ câu hỏi tự nhiên.

QUY TẮC QUAN TRỌNG:
1. CHỈ trích xuất TÊN PHIM THỰC SỰ - KHÔNG lấy các từ hỏi/phụ
2. Loại bỏ: "có", "không", "nào", "về", "muốn", "xem", "tìm", "gì", "đang", "chiếu"
3. Nếu hỏi "phim đang chiếu" / "phim gì chiếu" → KHÔNG có query, chỉ want_showtime: true
4. Nếu hỏi về THỂ LOẠI (hành động, kinh dị...) → dùng "genre" (tiếng Anh)

VÍ DỤ QUAN TRỌNG:
- "có phim nào về Batman không" → {{"query": "Batman"}}
- "phim batman" → {{"query": "batman"}}
- "tìm phim The Godfather" → {{"query": "The Godfather"}}
- "có phim hành động nào hay không" → {{"genre": "Action"}}
- "phim gì đang chiếu" → {{"want_showtime": true}}
- "tôi muốn xem các phim đang chiếu" → {{"want_showtime": true}}
- "lịch chiếu phim Avatar" → {{"query": "Avatar", "want_showtime": true}}
- "gợi ý 3 phim hành động" → {{"genre": "Action", "limit": 3}}

SAI - KHÔNG LÀM:
- "có phim nào về Batman không" → {{"query": "có nào về batman không"}} ❌
- "tôi muốn xem các phim đang chiếu" → {{"query": "đang"}} ❌

CHỈ trả JSON ngắn gọn."""
        
        self.response_instruction = f"""Bạn là chuyên gia tư vấn phim ảnh thân thiện.

{knowledge_service.get_system_knowledge()}

NGUYÊN TẮC QUAN TRỌNG (KHÔNG BỊA ĐẶT):
- CHỈ dùng thông tin từ DATABASE được cung cấp
- KHÔNG tự nghĩ ra phim không có trong data
- Nếu không tìm thấy → nói thật "không có trong hệ thống"

Format response:
🎬 **Tên Phim** (Năm) - ⭐ Rating/10
📝 Mô tả ngắn
🎭 Thể loại | 🎬 Đạo diễn | ⏱️ Thời lượng

Trả lời bằng tiếng Việt."""
        
        self.extraction_model = gemini_service.create_model(self.extraction_instruction)
        self.response_model = gemini_service.create_model(self.response_instruction)
    
    async def process(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Xử lý yêu cầu về phim"""
        
        message_lower = message.lower()
        
        # Handle vague requests FIRST - "phim hot", "phim hay", "có phim gì"
        vague_patterns = ["phim hot", "phim hay", "phim nào hot", "phim gì hay", "có phim gì", "có phim nào"]
        if any(p in message_lower for p in vague_patterns):
            return await self._handle_movie_suggestion(state)
        
        # Extract search parameters
        params = await self._extract_search_params(message)
        print(f"[MovieAgent] Extracted params: {params}")
        
        # If no params extracted or empty query, show suggestions
        if not params or (not params.get("query") and not params.get("genre") and not params.get("want_showtime")):
            return await self._handle_movie_suggestion(state)
        
        # Translate Vietnamese genre to English
        if params.get("genre"):
            translated = knowledge_service.translate_genre_vi_to_en(params["genre"])
            if translated:
                params["genre"] = translated
        
        # SCENARIO 3: Hỏi lịch chiếu/giá vé
        if params.get("want_showtime"):
            return await self._handle_showtime_query(message, params, state)
        
        # SCENARIO 1, 2, 7: Tìm kiếm phim
        movies_data = await self._search_movies(params, message)
        
        # Lưu context phim đã tìm được
        if movies_data.get("movies"):
            self._save_movie_context(movies_data["movies"], state)
        
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
    
    async def _handle_movie_suggestion(self, state: AgentState) -> Dict[str, Any]:
        """Handle vague movie requests with top suggestions"""
        movies = await api_client.get_movies(page=1, page_size=5, sort_by="imdb_rating")
        movies_list = movies.get("items", [])
        
        if movies_list:
            # Save to context
            self._save_movie_context(movies_list, state)
            
            movie_text = "\n".join([
                f"{i}. 🎬 **{m.get('series_title')}** ({m.get('released_year', 'N/A')}) - ⭐ {m.get('imdb_rating', 'N/A')}"
                for i, m in enumerate(movies_list, 1)
            ])
            return {
                "response": f"""🔥 **Top phim hay nhất:**

{movie_text}

💡 Bạn muốn:
- Xem chi tiết? Nói "Kể về phim số 1"
- Xem lịch chiếu? Nói "Lịch chiếu phim [tên]"
- Tìm thể loại khác? Nói "Phim hành động" hoặc "Phim kinh dị\"""",
                "agent": self.name,
                "metadata": {"intent": "movie_suggestion", "count": len(movies_list)}
            }
        
        return {
            "response": "Hiện không có phim nào trong hệ thống. Vui lòng thử lại sau!",
            "agent": self.name,
            "metadata": {"error": "no_movies"}
        }
    
    async def can_handle(self, message: str, state: AgentState) -> bool:
        """Check if this agent can handle the message"""
        keywords = ["phim", "movie", "xem", "gợi ý", "tìm", "thể loại", 
                   "diễn viên", "đạo diễn", "lịch chiếu", "giá vé", "suất chiếu"]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in keywords)
    
    async def _handle_showtime_query(
        self, 
        message: str, 
        params: Dict, 
        state: AgentState
    ) -> Dict[str, Any]:
        """SCENARIO 3: Xử lý hỏi lịch chiếu/giá vé"""
        
        movie_id = None
        movie_title = None
        
        # Tìm phim nếu có query
        if params.get("query"):
            movies = await api_client.search_movies(params["query"], limit=1)
            if movies:
                movie_id = movies[0].get("id")
                movie_title = movies[0].get("series_title")
        
        # Parse date
        date = api_client.parse_date_from_text(message)
        
        # Lấy showtimes
        showtimes = await api_client.get_showtimes(
            movie_id=movie_id,
            date=date
        )
        
        if not showtimes:
            if movie_title:
                return {
                    "response": f"""❌ Không tìm thấy suất chiếu cho phim **{movie_title}**{f' ngày {date}' if date else ''}.

Có thể phim chưa có lịch chiếu hoặc đã hết suất.

Bạn muốn:
🔍 Tìm phim khác?
📅 Xem lịch chiếu ngày khác?""",
                    "agent": self.name,
                    "metadata": {"no_showtimes": True}
                }
            else:
                return {
                    "response": """Bạn muốn xem lịch chiếu phim nào? Cho tôi biết:
- Tên phim (VD: "lịch chiếu Avatar")
- Hoặc ngày xem (VD: "phim chiếu hôm nay")""",
                    "agent": self.name,
                    "metadata": {"need_more_info": True}
                }
        
        # Format showtimes response
        response = self._format_showtimes_response(showtimes, movie_title, date)
        
        return {
            "response": response,
            "agent": self.name,
            "metadata": {
                "showtimes_count": len(showtimes),
                "movie_title": movie_title
            }
        }
    
    def _format_showtimes_response(
        self, 
        showtimes: List[Dict], 
        movie_title: Optional[str],
        date: Optional[str]
    ) -> str:
        """Format showtimes for display"""
        
        header = f"📅 **Lịch chiếu"
        if movie_title:
            header += f" - {movie_title}"
        if date:
            header += f" ({date})"
        header += "**\n\n"
        
        # Group by cinema
        by_cinema = {}
        for st in showtimes:
            cinema = st.get("cinema_name", "Rạp")
            if cinema not in by_cinema:
                by_cinema[cinema] = []
            by_cinema[cinema].append(st)
        
        lines = [header]
        for cinema, sts in by_cinema.items():
            lines.append(f"🏛️ **{cinema}**")
            for st in sts[:5]:  # Max 5 per cinema
                time_str = st.get("start_time", "N/A")
                price = st.get("base_price", 0)
                lines.append(f"  🕐 {time_str} - 💰 {price:,.0f}đ")
            lines.append("")
        
        lines.append("💡 Để đặt vé, hãy nói: \"Đặt vé phim [tên phim]\"")
        
        return "\n".join(lines)
    
    async def _extract_search_params(self, message: str) -> Dict[str, Any]:
        """Extract search parameters with fallback"""
        
        try:
            prompt = f"""Tin nhắn: "{message}"

Trích xuất thông tin:
- query: Tên phim cụ thể
- genre: Thể loại (tiếng Anh)
- limit: Số lượng phim yêu cầu
- want_showtime: true nếu hỏi lịch chiếu/giá vé
- min_rating: Rating tối thiểu

Trả về JSON ngắn gọn."""
            
            response = self.extraction_model.generate_content(prompt)
            text = response.text.strip()
            
            # Clean JSON
            if text.startswith("```"):
                text = re.sub(r'^```\w*\n?', '', text)
                text = re.sub(r'\n?```$', '', text)
            
            result = json.loads(text.strip())
            if isinstance(result, dict):
                return result
                
        except Exception as e:
            print(f"[MovieAgent] Extraction error: {e}")
        
        return self._simple_extraction(message)
    
    def _simple_extraction(self, message: str) -> Dict[str, Any]:
        """FALLBACK: Rule-based extraction - smarter"""
        message_lower = message.lower()
        params = {}
        
        # Detect "đang chiếu" intent FIRST - this is showtime query, not movie search
        showing_patterns = ["đang chiếu", "phim gì chiếu", "chiếu phim gì", "các phim chiếu", "phim nào chiếu"]
        if any(p in message_lower for p in showing_patterns):
            params["want_showtime"] = True
            return params  # Return early - don't try to extract movie name
        
        # Detect genre
        genre_map = {
            "hoạt hình": "Animation", "hành động": "Action",
            "phiêu lưu": "Adventure", "hài": "Comedy",
            "tâm lý": "Drama", "kinh dị": "Horror",
            "khoa học viễn tưởng": "Sci-Fi", "tình cảm": "Romance",
            "tội phạm": "Crime", "chiến tranh": "War"
        }
        
        for vn, en in genre_map.items():
            if vn in message_lower:
                params["genre"] = en
                break
        
        # Detect quantity
        match = re.search(r'(\d+)\s*phim', message_lower)
        if match:
            params["limit"] = int(match.group(1))
        
        # Detect showtime intent
        if any(w in message_lower for w in ["lịch chiếu", "giá vé", "suất chiếu", "chiếu lúc"]):
            params["want_showtime"] = True
        
        # Extract movie name - remove noise words
        if not params.get("genre"):
            query = self._extract_movie_query(message)
            if query and len(query) > 1:
                params["query"] = query
        
        return params
    
    def _extract_movie_query(self, message: str) -> Optional[str]:
        """Extract actual movie name from natural question"""
        
        # Noise words to remove
        noise_words = [
            "có", "không", "nào", "về", "muốn", "xem", "tìm", "gì", 
            "đang", "chiếu", "phim", "hay", "tôi", "mình", "bạn",
            "cho", "biết", "được", "ơi", "à", "ạ", "nhé", "nha",
            "thế", "thì", "là", "và", "hoặc", "với", "của", "các",
            "những", "một", "cái", "bộ", "lịch", "suất", "vé", "giá"
        ]
        
        # Try pattern matching first for "về X", "phim X"
        patterns = [
            r'về\s+([A-Za-z0-9\s]+?)(?:\s+không|\s+nào|$)',
            r'phim\s+([A-Za-z][A-Za-z0-9\s:]+?)(?:\s+có|\s+không|\s+chiếu|$)',
            r'lịch chiếu\s+(?:phim\s+)?([A-Za-z][A-Za-z0-9\s:]+?)(?:\s+hôm|\s+ngày|$)',
            r'tìm\s+(?:phim\s+)?([A-Za-z][A-Za-z0-9\s:]+?)(?:\s+có|\s+không|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean trailing noise
                for word in noise_words:
                    name = re.sub(rf'\s+{word}$', '', name, flags=re.IGNORECASE)
                if name and len(name) > 1:
                    return name
        
        # Fallback: remove all noise words
        words = message.lower().split()
        clean_words = [w for w in words if w not in noise_words and len(w) > 1]
        
        if clean_words:
            return ' '.join(clean_words)
        
        return None
    
    async def _search_movies(self, params: Dict[str, Any], original_message: str) -> Dict[str, Any]:
        """Search movies with multiple strategies"""
        
        limit = params.get("limit", 5)
        
        # Strategy 1: Search by query
        if params.get("query"):
            query = params["query"]
            
            # Try exact search first
            movies = await api_client.search_movies(query=query, limit=limit)
            
            if movies:
                return {"movies": movies, "total": len(movies), "method": "exact"}
            
            # SCENARIO 7: Fuzzy search fallback
            fuzzy_result = await api_client.fuzzy_search_movie(query)
            if fuzzy_result.get("found"):
                movie = fuzzy_result["movie"]
                confidence = fuzzy_result["confidence"]
                
                # Nếu confidence < 80%, hỏi xác nhận
                if confidence < 80:
                    return {
                        "movies": [movie],
                        "total": 1,
                        "method": "fuzzy",
                        "need_confirm": True,
                        "original_query": query,
                        "matched_title": fuzzy_result["matched_title"],
                        "confidence": confidence
                    }
                return {"movies": [movie], "total": 1, "method": "fuzzy"}
        
        # Strategy 2: Filter by genre/rating
        if params.get("genre") or params.get("min_rating"):
            response = await api_client.get_movies(
                page=1,
                page_size=limit,
                genre=params.get("genre"),
                min_rating=params.get("min_rating"),
                sort_by="rating"
            )
            movies = response.get("items", [])
            if movies:
                return {"movies": movies, "total": response.get("total", len(movies)), "method": "filter"}
        
        return {"movies": [], "total": 0, "method": "none"}
    
    def _save_movie_context(self, movies: List[Dict], state: AgentState):
        """Lưu context phim để dùng cho Scenario 5"""
        if not state.movie_context:
            state.movie_context = MovieContext()
        
        state.movie_context.movie_ids = [str(m.get("id")) for m in movies]
        state.movie_context.movie_titles = [m.get("series_title", "") for m in movies]
    
    async def _generate_movie_response(
        self,
        message: str,
        movies_data: Dict[str, Any],
        state: AgentState
    ) -> str:
        """Generate response based on search results"""
        
        movies = movies_data.get("movies", [])
        
        # SCENARIO 7: Fuzzy match cần xác nhận
        if movies_data.get("need_confirm"):
            movie = movies[0]
            return f"""🔍 Bạn có phải muốn tìm phim **{movies_data['matched_title']}** không?

(Tôi không tìm thấy "{movies_data['original_query']}" chính xác trong database)

🎬 **{movie.get('series_title')}** ({movie.get('released_year')})
⭐ Rating: {movie.get('imdb_rating')}/10
🎭 Thể loại: {movie.get('genre')}

Trả lời "có" để xem chi tiết, hoặc thử tìm với tên khác."""
        
        if not movies:
            return """❌ Không tìm thấy phim phù hợp trong database.

Bạn có thể thử:
- Tìm với từ khóa khác (VD: "phim hành động")
- Kiểm tra lại tên phim
- Hỏi "có những phim nào" để xem danh sách

⚠️ Tôi chỉ tìm trong database CÓ SẴN, không tự nghĩ ra phim!"""
        
        # Format movie info
        movies_info = self._format_movies_info(movies[:5])
        
        prompt = f"""User hỏi: "{message}"

DATABASE TÌM ĐƯỢC ({len(movies)} phim):
{movies_info}

NHIỆM VỤ:
- Gợi ý phim từ kết quả trên
- Dùng ĐÚNG thông tin database
- Format đẹp với emoji

Trả lời tiếng Việt."""
        
        try:
            response = self.response_model.generate_content(prompt)
            return response.text
        except Exception as e:
            # Fallback response
            movie = movies[0]
            return f"""📊 Tìm thấy {len(movies)} phim!

🎬 **{movie.get('series_title')}** ({movie.get('released_year')})
⭐ Rating: {movie.get('imdb_rating')}/10
🎭 Thể loại: {movie.get('genre')}
🎬 Đạo diễn: {movie.get('director')}

📝 {movie.get('overview', 'Một bộ phim hay!')[:200]}..."""
    
    def _format_movies_info(self, movies: List[Dict]) -> str:
        """Format movies for prompt"""
        formatted = []
        for m in movies:
            info = f"""- **{m.get('series_title')}** ({m.get('released_year')})
  Rating: {m.get('imdb_rating')}/10 | Thể loại: {m.get('genre')}
  Đạo diễn: {m.get('director')}
  Mô tả: {(m.get('overview') or '')[:150]}..."""
            formatted.append(info)
        return "\n".join(formatted)
