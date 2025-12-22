# app/services/api_client.py
import httpx
from typing import Dict, Any, List, Optional
from app.config import settings

class APIClient:
    """Client để gọi các microservices khác"""
    
    def __init__(self):
        self.movie_service_url = settings.MOVIE_SERVICE_URL
        self.booking_service_url = settings.BOOKING_SERVICE_URL
        self.cinema_service_url = settings.CINEMA_SERVICE_URL
        self.timeout = 30.0
    
    async def search_movies(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search movies by query"""
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
    
    async def get_movies(
        self,
        page: int = 1,
        page_size: int = 10,
        genre: Optional[str] = None,
        year: Optional[str] = None,
        min_rating: Optional[float] = None,
        sort_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get paginated movies with filters"""
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
        """Get movie detail by ID"""
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
    
    async def get_showtimes(
        self,
        movie_id: Optional[int] = None,
        cinema_id: Optional[int] = None,
        date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get showtimes"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {}
                if movie_id:
                    params["movie_id"] = movie_id
                if cinema_id:
                    params["cinema_id"] = cinema_id
                if date:
                    params["date"] = date
                    
                response = await client.get(
                    f"{self.cinema_service_url}/api/v1/showtimes",
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error getting showtimes: {e}")
            return []
    
    async def get_available_seats(self, showtime_id: int) -> List[Dict[str, Any]]:
        """Get available seats for showtime"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.cinema_service_url}/api/v1/showtimes/{showtime_id}/seats"
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error getting seats: {e}")
            return []
    
    async def create_booking(
        self,
        user_id: str,
        showtime_id: int,
        seat_ids: List[int],
        token: str
    ) -> Optional[Dict[str, Any]]:
        """Create booking"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.booking_service_url}/api/v1/bookings",
                    json={
                        "showtime_id": showtime_id,
                        "seat_ids": seat_ids
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error creating booking: {e}")
            return None


# Singleton instance
api_client = APIClient()