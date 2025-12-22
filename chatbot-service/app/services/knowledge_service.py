# app/services/knowledge_service.py
import pandas as pd
import os
from typing import Dict, List, Optional
from pathlib import Path

class KnowledgeService:
    """Service để quản lý knowledge base"""
    
    def __init__(self):
        self.knowledge_dir = Path(__file__).parent.parent / "knowledges"
        self.movies_df = None
        self.genre_mapping = self._load_genre_mapping()
        self.system_info = self._load_system_info()
        self._load_movies()
    
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
            f"Thể loại có sẵn: {', '.join(self.get_all_genres()[:20])}"  # First 20
        ]
        return "\n".join(knowledge)


# Singleton instance
knowledge_service = KnowledgeService()