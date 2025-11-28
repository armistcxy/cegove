from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.movie import (
    MovieCreate, MovieUpdate, MovieResponse, 
    PaginationParams, PaginatedResponse,
    GenreStats, DirectorStats, YearStats, 
    RatingDistribution, DashboardStats
)
from app.services.movie_service import MovieService
from app.api.deps import get_current_user, require_admin
import math

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[MovieResponse])
def get_movies(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    search: Optional[str] = Query(None, description="Full-text search query"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    year: Optional[str] = Query(None, description="Filter by year"),
    min_rating: Optional[float] = Query(None, ge=0, le=10, description="Minimum IMDB rating"),
    db: Session = Depends(get_db)
    # Không yêu cầu authentication - Public endpoint
):
    """
    Get paginated list of movies with advanced filtering and sorting
    
    **Public endpoint** - No authentication required
    
    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page (max 100)
    - **sort_by**: Field to sort by (rating, released_year, meta_score, etc.)
    - **sort_order**: asc or desc
    - **search**: Full-text search in title, overview, director, genre
    - **genre**: Filter by genre (partial match)
    - **year**: Filter by exact release year
    - **min_rating**: Filter movies with rating >= this value
    """
    params = PaginationParams(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    movies, total = MovieService.get_movies_paginated(
        db=db,
        params=params,
        search=search,
        genre=genre,
        year=year,
        min_rating=min_rating
    )
    
    total_pages = math.ceil(total / page_size)
    
    return PaginatedResponse(
        items=movies,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


@router.get("/{movie_id}", response_model=MovieResponse)
def get_movie(
    movie_id: int,
    db: Session = Depends(get_db)
    # Không yêu cầu authentication - Public endpoint
):
    """
    Get movie by ID
    
    **Public endpoint** - No authentication required
    """
    movie = MovieService.get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.post("/", response_model=MovieResponse, status_code=201)
def create_movie(
    movie: MovieCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)  # Chỉ Admin
):
    """
    Create new movie with validation
    
    **Admin only**
    
    Validations:
    - series_title and overview are required
    - released_year must be between 1900-2030
    - imdb_rating must be between 0-10
    - meta_score must be between 0-100
    - runtime must be > 0
    """
    return MovieService.create_movie(db, movie)


@router.put("/{movie_id}", response_model=MovieResponse)
def update_movie(
    movie_id: int,
    movie: MovieUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)  # Chỉ Admin
):
    """
    Update existing movie
    
    **Admin only**
    """
    updated_movie = MovieService.update_movie(db, movie_id, movie)
    if not updated_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return updated_movie


@router.delete("/{movie_id}", status_code=204)
def delete_movie(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)  # Chỉ Admin
):
    """
    Delete movie by ID
    
    **Admin only**
    """
    success = MovieService.delete_movie(db, movie_id)
    if not success:
        raise HTTPException(status_code=404, detail="Movie not found")
    return None


# ==================== DASHBOARD/STATS ENDPOINTS ====================

@router.get("/stats/overview", response_model=DashboardStats)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # Yêu cầu đăng nhập
):
    """
    Get overall dashboard statistics
    
    **Authentication required** - User hoặc Admin
    
    Returns:
    - Total movies, directors, genres
    - Average rating and meta score
    """
    stats = MovieService.get_dashboard_stats(db)
    return stats


@router.get("/stats/by-genre", response_model=List[GenreStats])
def get_stats_by_genre(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # Yêu cầu đăng nhập
):
    """
    Get statistics by genre
    
    **Authentication required** - User hoặc Admin
    
    Returns list of genres with:
    - Number of movies
    - Average rating
    """
    return MovieService.get_stats_by_genre(db)


@router.get("/stats/top-directors", response_model=List[DirectorStats])
def get_top_directors(
    limit: int = Query(10, ge=1, le=50, description="Number of directors to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # Yêu cầu đăng nhập
):
    """
    Get top directors by average rating
    
    **Authentication required** - User hoặc Admin
    
    Returns directors with:
    - Number of movies
    - Average rating
    - Total votes
    
    Only includes directors with at least 2 movies
    """
    return MovieService.get_top_directors(db, limit)


@router.get("/stats/by-year", response_model=List[YearStats])
def get_movies_per_year(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # Yêu cầu đăng nhập
):
    """
    Get number of movies per year
    
    **Authentication required** - User hoặc Admin
    
    Useful for timeline charts
    """
    return MovieService.get_movies_per_year(db)


@router.get("/stats/rating-distribution", response_model=List[RatingDistribution])
def get_rating_distribution(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # Yêu cầu đăng nhập
):
    """
    Get IMDB rating distribution histogram
    
    **Authentication required** - User hoặc Admin
    
    Returns count of movies in ranges: 0-1, 1-2, ..., 9-10
    """
    return MovieService.get_rating_distribution(db)


@router.get("/stats/meta-score-distribution", response_model=List[RatingDistribution])
def get_meta_score_distribution(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # Yêu cầu đăng nhập
):
    """
    Get Meta Score distribution histogram
    
    **Authentication required** - User hoặc Admin
    
    Returns count of movies in ranges: 0-10, 10-20, ..., 90-100
    """
    return MovieService.get_meta_score_distribution(db)