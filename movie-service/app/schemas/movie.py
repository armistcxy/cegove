from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Generic, TypeVar
from datetime import datetime
import re

T = TypeVar('T')


class MovieBase(BaseModel):
    poster_link: Optional[str] = None
    series_title: str = Field(..., min_length=1, max_length=255)
    released_year: Optional[str] = None
    certificate: Optional[str] = None
    runtime: Optional[str] = None
    genre: Optional[str] = None
    imdb_rating: Optional[float] = Field(None, ge=0, le=10)
    overview: Optional[str] = None
    meta_score: Optional[int] = Field(None, ge=0, le=100)
    director: Optional[str] = None
    star1: Optional[str] = None
    star2: Optional[str] = None
    star3: Optional[str] = None
    star4: Optional[str] = None
    no_of_votes: Optional[int] = None
    gross: Optional[str] = None


class MovieCreate(MovieBase):
    series_title: str = Field(..., min_length=1, max_length=255, description="Title is required")
    overview: str = Field(..., min_length=1, description="Overview is required")
    
    @field_validator('released_year')
    @classmethod
    def validate_year(cls, v):
        """Validate released year is between 1900-2030"""
        if v is not None:
            try:
                year = int(v)
                if year < 1900 or year > 2030:
                    raise ValueError('Released year must be between 1900 and 2030')
            except ValueError:
                raise ValueError('Released year must be a valid number')
        return v
    
    @field_validator('runtime')
    @classmethod
    def validate_runtime(cls, v):
        """Validate runtime is positive"""
        if v is not None:
            # Extract numeric value from runtime string (e.g., "120 min" -> 120)
            match = re.search(r'\d+', str(v))
            if match:
                runtime_value = int(match.group())
                if runtime_value <= 0:
                    raise ValueError('Runtime must be greater than 0')
        return v
    
    @field_validator('imdb_rating')
    @classmethod
    def validate_rating(cls, v):
        """Validate IMDB rating is between 0-10"""
        if v is not None and (v < 0 or v > 10):
            raise ValueError('IMDB rating must be between 0 and 10')
        return v
    
    @field_validator('meta_score')
    @classmethod
    def validate_meta_score(cls, v):
        """Validate meta score is between 0-100"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Meta score must be between 0 and 100')
        return v


class MovieUpdate(BaseModel):
    poster_link: Optional[str] = None
    series_title: Optional[str] = Field(None, min_length=1, max_length=255)
    released_year: Optional[str] = None
    certificate: Optional[str] = None
    runtime: Optional[str] = None
    genre: Optional[str] = None
    imdb_rating: Optional[float] = Field(None, ge=0, le=10)
    overview: Optional[str] = None
    meta_score: Optional[int] = Field(None, ge=0, le=100)
    director: Optional[str] = None
    star1: Optional[str] = None
    star2: Optional[str] = None
    star3: Optional[str] = None
    star4: Optional[str] = None
    no_of_votes: Optional[int] = None
    gross: Optional[str] = None


class MovieResponse(MovieBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    class Config:
        from_attributes = True


class GenreStats(BaseModel):
    """Statistics by genre"""
    genre: str
    count: int
    avg_rating: Optional[float]


class DirectorStats(BaseModel):
    """Director statistics"""
    director: str
    movie_count: int
    avg_rating: Optional[float]
    total_votes: Optional[int]


class YearStats(BaseModel):
    """Movies per year statistics"""
    year: str
    count: int


class RatingDistribution(BaseModel):
    """Rating distribution"""
    rating_range: str
    count: int


class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_movies: int
    total_directors: int
    total_genres: int
    avg_rating: Optional[float]
    avg_meta_score: Optional[float]