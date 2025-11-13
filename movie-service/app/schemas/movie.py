from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


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
    pass


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