# app/services/api_client.py
import httpx
from typing import Dict, Any, List, Optional
from app.config import settings
from fuzzywuzzy import fuzz, process
from datetime import datetime, timedelta

class APIClient:
    """Client để gọi các microservices khác"""
    
    def __init__(self):
        self.movie_service_url = settings.MOVIE_SERVICE_URL
        self.booking_service_url = settings.BOOKING_SERVICE_URL
        self.cinema_service_url = settings.CINEMA_SERVICE_URL
        self.payment_service_url = settings.PAYMENT_SERVICE_URL
        self.timeout = 30.0
    
    # ========== MOVIE SERVICE APIs ==========
    
    async def search_movies(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search movies by query - Scenario 1, 7 (Fuzzy Search)"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.movie_service_url}/api/v1/movies/search",
                    params={"q": query, "limit": limit}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error searching movies: {e}")
            return []
    
    async def fuzzy_search_movie(self, query: str, threshold: int = 60) -> Dict[str, Any]:
        """
        Fuzzy search for movie - Scenario 7 (Error Handling)
        Trả về best match và confidence score
        """
        try:
            # Lấy tất cả phim
            all_movies = await self.get_movies(page=1, page_size=100)
            movies_list = all_movies.get("items", [])
            
            if not movies_list:
                return {"found": False, "suggestion": None}
            
            # Tạo list titles để match
            titles = [m.get("series_title", "") for m in movies_list]
            
            # Fuzzy match
            best_match = process.extractOne(query, titles, scorer=fuzz.token_set_ratio)
            
            if best_match and best_match[1] >= threshold:
                # Tìm movie data
                matched_title = best_match[0]
                matched_movie = next(
                    (m for m in movies_list if m.get("series_title") == matched_title), 
                    None
                )
                return {
                    "found": True,
                    "movie": matched_movie,
                    "confidence": best_match[1],
                    "original_query": query,
                    "matched_title": matched_title
                }
            
            return {"found": False, "suggestion": best_match[0] if best_match else None}
            
        except Exception as e:
            print(f"Error in fuzzy search: {e}")
            return {"found": False, "error": str(e)}
    
    async def get_movies(
        self,
        page: int = 1,
        page_size: int = 10,
        genre: Optional[str] = None,
        year: Optional[str] = None,
        min_rating: Optional[float] = None,
        sort_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get paginated movies with filters - Scenario 2"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    "page": page,
                    "page_size": page_size
                }
                if genre:
                    params["genre"] = genre
                if year:
                    params["year"] = year
                if min_rating:
                    params["min_rating"] = min_rating
                if sort_by:
                    params["sort_by"] = sort_by
                    
                response = await client.get(
                    f"{self.movie_service_url}/api/v1/movies/",
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error getting movies: {e}")
            return {"items": [], "total": 0}
    
    async def get_movie_detail(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Get movie detail by ID - Scenario 1, 5"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.movie_service_url}/api/v1/movies/{movie_id}"
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error getting movie detail: {e}")
            return None
    
    # ========== BOOKING SERVICE APIs ==========
    
    async def get_showtimes(
        self,
        movie_id: Optional[int] = None,
        cinema_id: Optional[int] = None,
        date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get showtimes with optional filters - Scenario 3, 4
        API: /api/v1/showtimes?movie_id=X&cinema_id=Y&date=YYYY-MM-DD
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {}
                if movie_id is not None:
                    params["movie_id"] = movie_id
                if cinema_id is not None:
                    params["cinema_id"] = cinema_id
                if date is not None:
                    params["date"] = date
                
                response = await client.get(
                    f"{self.booking_service_url}/api/v1/showtimes",
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error getting showtimes: {e}")
            return []
    
    async def get_showtimes_by_cinema_name(
        self, 
        cinema_name: str,
        date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get showtimes for a specific cinema by name.
        Useful when user asks "Rạp CGV Times City chiếu phim gì?"
        """
        from app.services.knowledge_service import knowledge_service
        
        # Tìm cinema ID từ tên
        cinemas = knowledge_service.search_cinema(cinema_name)
        if not cinemas:
            return []
        
        cinema_id = cinemas[0].get("id")
        return await self.get_showtimes(cinema_id=cinema_id, date=date)
    
    async def get_showtimes_by_movie_name(
        self, 
        movie_name: str,
        cinema_id: Optional[int] = None,
        date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get showtimes for a specific movie by name.
        Useful when user asks "Phim Avengers chiếu lúc mấy giờ?"
        """
        # Tìm movie ID từ tên
        result = await self.fuzzy_search_movie(movie_name)
        if not result.get("found"):
            return []
        
        movie_id = result.get("movie", {}).get("id")
        if not movie_id:
            return []
        
        return await self.get_showtimes(
            movie_id=movie_id, 
            cinema_id=cinema_id, 
            date=date
        )
    
    async def get_showtime_seats(self, showtime_id: str) -> List[Dict[str, Any]]:
        """Get seats for showtime - Scenario 4, 8"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.booking_service_url}/api/showtimes/{showtime_id}/seats"
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error getting seats: {e}")
            return []
    
    async def get_showtime_seats_v2(self, showtime_id: str) -> List[Dict[str, Any]]:
        """Get seats V2 with rich data - Scenario 4, 8 (Real-time availability)"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.booking_service_url}/api/v2/showtimes/{showtime_id}/seats"
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error getting seats v2: {e}")
            return []
    
    async def get_available_seats_count(self, showtime_id: str) -> Dict[str, Any]:
        """
        Get available seats count - Scenario 8
        Trả về số ghế còn trống theo loại
        """
        try:
            seats = await self.get_showtime_seats_v2(showtime_id)
            
            total_available = 0
            by_type = {}
            
            for seat in seats:
                status = seat.get("status_text", "").lower()
                seat_type = seat.get("metadata", {}).get("type_code", "STANDARD")
                
                if status == "available":
                    total_available += 1
                    by_type[seat_type] = by_type.get(seat_type, 0) + 1
            
            return {
                "total_available": total_available,
                "by_type": by_type,
                "total_seats": len(seats)
            }
        except Exception as e:
            print(f"Error counting available seats: {e}")
            return {"total_available": 0, "by_type": {}, "error": str(e)}
    
    async def create_booking(
        self,
        user_id: str,
        showtime_id: str,
        seat_ids: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Create booking - Scenario 4"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.booking_service_url}/api/bookings",
                    json={
                        "user_id": user_id,
                        "showtime_id": showtime_id,
                        "seat_ids": seat_ids
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error creating booking: {e}")
            return None
    
    async def get_booking(self, booking_id: str) -> Optional[Dict[str, Any]]:
        """Get booking detail - Scenario 5 (history)"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.booking_service_url}/api/bookings/{booking_id}"
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error getting booking: {e}")
            return None
    
    async def get_user_bookings(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's booking history - Scenario 5"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.booking_service_url}/api/bookings",
                    params={"user_id": user_id}
                )
                response.raise_for_status()
                bookings = response.json()
                # Filter by user_id if needed
                return [b for b in bookings if b.get("user_id") == user_id]
        except Exception as e:
            print(f"Error getting user bookings: {e}")
            return []
    
    # ========== PAYMENT SERVICE APIs ==========
    
    async def create_payment(
        self,
        booking_id: str,
        amount: float,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Create payment for booking
        Returns payment URL or payment info
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.payment_service_url}/api/v1/payments/",
                    json={
                        "booking_id": booking_id,
                        "amount": amount,
                        "user_id": user_id
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error creating payment: {e}")
            return None
    
    # ========== HELPER METHODS ==========
    
    def parse_date_from_text(self, text: str) -> Optional[str]:
        """Parse date from Vietnamese text"""
        text_lower = text.lower()
        today = datetime.now()
        
        if "hôm nay" in text_lower or "today" in text_lower:
            return today.strftime("%Y-%m-%d")
        elif "ngày mai" in text_lower or "mai" in text_lower or "tomorrow" in text_lower:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "ngày kia" in text_lower:
            return (today + timedelta(days=2)).strftime("%Y-%m-%d")
        
        # Try to parse DD/MM format
        import re
        match = re.search(r'(\d{1,2})[/\-](\d{1,2})', text)
        if match:
            day, month = int(match.group(1)), int(match.group(2))
            year = today.year
            try:
                parsed_date = datetime(year, month, day)
                return parsed_date.strftime("%Y-%m-%d")
            except:
                pass
        
        return None


# Singleton instance
api_client = APIClient()