from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MovieRecommendation(BaseModel):
    """Movie recommendation response"""
    id: int
    series_title: str
    released_year: Optional[str] = None
    genre: Optional[str] = None
    imdb_rating: Optional[float] = None
    meta_score: Optional[int] = None
    director: Optional[str] = None
    poster_link: Optional[str] = None
    overview: Optional[str] = None
    no_of_votes: Optional[int] = None
    
    # Recommendation metadata
    similarity_score: Optional[float] = Field(None, description="Similarity score (0-1)")
    reason: Optional[str] = Field(None, description="Why this movie is recommended")
    
    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    """Recommendation response with metadata"""
    recommendations: List[MovieRecommendation]
    total: int
    method: str = Field(..., description="Recommendation method used")
    based_on_movie_id: Optional[int] = Field(None, description="Source movie ID for content-based")
    based_on_movie_title: Optional[str] = Field(None, description="Source movie title")


class PopularMoviesParams(BaseModel):
    """Parameters for popular movies"""
    limit: int = Field(default=10, ge=1, le=50, description="Number of movies to return")
    min_votes: int = Field(default=10000, ge=0, description="Minimum number of votes")
    
    
class TopRatedParams(BaseModel):
    """Parameters for top rated movies"""
    limit: int = Field(default=10, ge=1, le=50, description="Number of movies to return")
    min_votes: int = Field(default=5000, ge=0, description="Minimum number of votes")
    

class SimilarMoviesParams(BaseModel):
    """Parameters for similar movies (content-based)"""
    movie_id: int = Field(..., description="Movie ID to find similar movies")
    limit: int = Field(default=10, ge=1, le=50, description="Number of recommendations")