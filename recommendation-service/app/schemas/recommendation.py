from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class MovieRecommendation(BaseModel):
    """Unified movie recommendation response"""
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
    predicted_score: Optional[float] = Field(None, description="CF predicted score or similarity score")
    similarity_score: Optional[float] = Field(None, description="Content-based similarity score (deprecated, use predicted_score)")
    recommendation_type: Literal["collaborative", "content-based", "popularity", "hybrid"] = Field(
        default="popularity",
        description="Type of recommendation algorithm used"
    )
    reason: Optional[str] = Field(None, description="Explanation for recommendation")

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    """Unified response wrapper for all recommendation endpoints"""
    recommendations: List[MovieRecommendation]
    total: int
    method: str = Field(description="Algorithm method used")
    based_on_movie_id: Optional[int] = None
    based_on_movie_title: Optional[str] = None
    user_id: Optional[int] = None
    is_cold_start: Optional[bool] = None


class RecommendationRequest(BaseModel):
    """Unified request for personalized recommendations"""
    user_id: int
    top_n: int = Field(default=10, ge=1, le=50, description="Number of recommendations")
    collaborative_weight: float = Field(
        default=0.7, 
        ge=0.0, 
        le=1.0,
        description="Weight for collaborative filtering (0-1), remainder is content-based"
    )
    exclude_watched: bool = Field(default=True, description="Exclude movies user has already watched")


class CollaborativeRequest(BaseModel):
    """Request for pure collaborative filtering"""
    user_id: int
    top_n: int = Field(default=10, ge=1, le=50)


class ContentBasedRequest(BaseModel):
    """Request for content-based recommendations"""
    movie_id: int
    limit: int = Field(default=10, ge=1, le=50)


# Deprecated schemas for backward compatibility
class CollaborativeRecommendationRequest(CollaborativeRequest):
    """Deprecated: Use CollaborativeRequest instead"""
    pass


class CollaborativeRecommendationResponse(BaseModel):
    """Deprecated: Use MovieRecommendation instead"""
    movie_id: int
    predicted_score: float
    title: str
    recommendation_type: str
    reason: Optional[str] = None


class HybridRecommendationRequest(RecommendationRequest):
    """Deprecated: Use RecommendationRequest instead"""
    pass


# Query parameters
class PopularMoviesParams(BaseModel):
    limit: int = Field(default=10, ge=1, le=50)
    min_votes: int = Field(default=10000, ge=0)


class TopRatedParams(BaseModel):
    limit: int = Field(default=10, ge=1, le=50)
    min_votes: int = Field(default=5000, ge=0)


class SimilarMoviesParams(BaseModel):
    limit: int = Field(default=10, ge=1, le=50)