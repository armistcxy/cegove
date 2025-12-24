# app/services/knowledge_service.py
import pandas as pd
import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from fuzzywuzzy import fuzz

class KnowledgeService:
    """Service để quản lý knowledge base"""
    
    def __init__(self):
        self.knowledge_dir = Path(__file__).parent.parent / "knowledges"
        self.movies_df = None
        self._cinemas: List[Dict[str, Any]] = []
        self.genre_mapping = self._load_genre_mapping()
        self.system_info = self._load_system_info()
        self._load_movies()
        self._load_cinemas()
    
    def _load_genre_mapping(self) -> Dict[str, str]:
        """Map từ tiếng Việt sang tiếng Anh"""
        return {
            # Thể loại phim
            "hành động": "Action",
            "phiêu lưu": "Adventure",
            "hoạt hình": "Animation",
            "tiểu sử": "Biography",
            "hài": "Comedy",
            "tội phạm": "Crime",
            "tài liệu": "Documentary",
            "chính kịch": "Drama",
            "gia đình": "Family",
            "giả tưởng": "Fantasy",
            "lịch sử": "History",
            "kinh dị": "Horror",
            "nhạc kịch": "Musical",
            "bí ẩn": "Mystery",
            "lãng mạn": "Romance",
            "khoa học viễn tưởng": "Sci-Fi",
            "khoa học": "Sci-Fi",
            "thể thao": "Sport",
            "ly kỳ": "Thriller",
            "chiến tranh": "War",
            "miền tây": "Western",
            
            # Variations
            "hài hước": "Comedy",
            "kinh dị": "Horror",
            "kịch": "Drama",
            "tình cảm": "Romance",
        }
    
    def _load_system_info(self) -> str:
        """Load thông tin về hệ thống"""
        return """Hệ thống đặt vé xem phim CEGOVE:

**Thông tin chung:**
- Hệ thống đặt vé phim trực tuyến
- Hỗ trợ tìm kiếm phim, suất chiếu, đặt vé tự động
- Chatbot AI hỗ trợ 24/7

**Chức năng:**
1. Tìm kiếm phim theo thể loại, năm, rating
2. Xem chi tiết phim (đạo diễn, diễn viên, nội dung)
3. Đặt vé tự động (chọn phim → suất chiếu → ghế → thanh toán)
4. Gợi ý phim hay dựa trên sở thích

**Thể loại phim có sẵn:**
- Hành động (Action)
- Phiêu lưu (Adventure)
- Hoạt hình (Animation)
- Hài (Comedy)
- Tội phạm (Crime)
- Chính kịch (Drama)
- Giả tưởng (Fantasy)
- Kinh dị (Horror)
- Lãng mạn (Romance)
- Khoa học viễn tưởng (Sci-Fi)
- Ly kỳ (Thriller)
- Và nhiều thể loại khác...

**Lưu ý:**
- Tên phim trong hệ thống là tiếng Anh
- Có thể tìm bằng tiếng Việt, hệ thống sẽ tự động chuyển đổi"""
    
    def _load_movies(self):
        """Load movies CSV"""
        try:
            csv_path = self.knowledge_dir / "movies.csv"
            if csv_path.exists():
                self.movies_df = pd.read_csv(csv_path)
                print(f"✓ Loaded {len(self.movies_df)} movies from knowledge base")
            else:
                print(f"⚠ Movies CSV not found at {csv_path}")
        except Exception as e:
            print(f"Error loading movies CSV: {e}")
    
    def translate_genre_vi_to_en(self, genre_vi: str) -> Optional[str]:
        """Chuyển đổi thể loại từ tiếng Việt sang tiếng Anh"""
        genre_lower = genre_vi.lower().strip()
        return self.genre_mapping.get(genre_lower)
    
    def get_all_genres(self) -> List[str]:
        """Lấy danh sách tất cả thể loại (tiếng Anh)"""
        if self.movies_df is None:
            return []
        
        # Extract unique genres from CSV
        all_genres = set()
        for genres_str in self.movies_df['Genre'].dropna():
            genres = [g.strip() for g in str(genres_str).split(',')]
            all_genres.update(genres)
        
        return sorted(list(all_genres))
    
    def get_genre_mapping_text(self) -> str:
        """Trả về text mapping thể loại để dùng trong prompt"""
        lines = ["Mapping thể loại Việt → Anh:"]
        for vi, en in self.genre_mapping.items():
            lines.append(f"- {vi} → {en}")
        return "\n".join(lines)
    
    def get_system_knowledge(self) -> str:
        """Trả về toàn bộ knowledge để inject vào prompt"""
        knowledge = [
            self.system_info,
            "\n---\n",
            self.get_genre_mapping_text(),
            "\n---\n",
            f"Tổng số phim trong hệ thống: {len(self.movies_df) if self.movies_df is not None else 0}",
            f"Thể loại có sẵn: {', '.join(self.get_all_genres()[:20])}",  # First 20
            f"Số rạp chiếu: {len(self._cinemas)}"
        ]
        return "\n".join(knowledge)
    
    # ==================== CINEMA METHODS ====================
    
    def _load_cinemas(self) -> None:
        """Load cinema data from cinemas.json"""
        cinemas_path = self.knowledge_dir / "cinemas.json"
        try:
            if cinemas_path.exists():
                with open(cinemas_path, 'r', encoding='utf-8') as f:
                    self._cinemas = json.load(f)
                print(f"[KnowledgeService] Loaded {len(self._cinemas)} cinemas")
            else:
                print(f"[KnowledgeService] Warning: cinemas.json not found at {cinemas_path}")
                self._cinemas = []
        except Exception as e:
            print(f"[KnowledgeService] Error loading cinemas: {e}")
            self._cinemas = []
    
    @property
    def cinemas(self) -> List[Dict[str, Any]]:
        """Get all cinemas"""
        return self._cinemas
    
    def get_cinema_by_id(self, cinema_id: int) -> Optional[Dict[str, Any]]:
        """Get cinema by ID"""
        for cinema in self._cinemas:
            if cinema.get('id') == cinema_id:
                return cinema
        return None
    
    def get_cinemas_by_city(self, city: str) -> List[Dict[str, Any]]:
        """Get all cinemas in a city (case-insensitive, partial match)"""
        city_lower = city.lower().strip()
        results = []
        for cinema in self._cinemas:
            cinema_city = cinema.get('city', '').lower()
            if city_lower in cinema_city or cinema_city in city_lower:
                results.append(cinema)
        return results
    
    def get_cinemas_by_district(self, district: str) -> List[Dict[str, Any]]:
        """Get all cinemas in a district (case-insensitive, partial match)"""
        district_lower = district.lower().strip()
        results = []
        for cinema in self._cinemas:
            cinema_district = cinema.get('district', '').lower()
            if district_lower in cinema_district or cinema_district in district_lower:
                results.append(cinema)
        return results
    
    def search_cinema(self, query: str, threshold: int = 60) -> List[Dict[str, Any]]:
        """
        Search cinemas by name using fuzzy matching
        Returns list of (cinema, score) sorted by score descending
        """
        query_lower = query.lower().strip()
        results = []
        
        for cinema in self._cinemas:
            cinema_name = cinema.get('name', '').lower()
            # Check exact substring match first
            if query_lower in cinema_name:
                results.append((cinema, 100))
                continue
            
            # Fuzzy match
            score = fuzz.partial_ratio(query_lower, cinema_name)
            if score >= threshold:
                results.append((cinema, score))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return [cinema for cinema, score in results]
    
    def get_unique_cities(self) -> List[str]:
        """Get list of unique cities where cinemas are located"""
        cities = set()
        for cinema in self._cinemas:
            city = cinema.get('city', '')
            if city:
                cities.add(city)
        return sorted(list(cities))
    
    def format_cinema_info(self, cinema: Dict[str, Any]) -> str:
        """Format cinema info for display"""
        return (
            f"🎬 {cinema.get('name', 'N/A')}\n"
            f"📍 {cinema.get('address', 'N/A')}, {cinema.get('district', '')}, {cinema.get('city', '')}\n"
            f"📞 {cinema.get('phone', 'N/A')}"
        )
    
    def get_cinema_list_text(self, cinemas: List[Dict[str, Any]], max_items: int = 10) -> str:
        """Format list of cinemas for display"""
        if not cinemas:
            return "Không tìm thấy rạp chiếu phim nào."
        
        lines = [f"Tìm thấy {len(cinemas)} rạp chiếu:"]
        for i, cinema in enumerate(cinemas[:max_items], 1):
            lines.append(f"\n{i}. {self.format_cinema_info(cinema)}")
        
        if len(cinemas) > max_items:
            lines.append(f"\n... và {len(cinemas) - max_items} rạp khác.")
        
        return "\n".join(lines)


# Singleton instance
knowledge_service = KnowledgeService()