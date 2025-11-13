from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.movie import MovieCreate, MovieUpdate, MovieResponse
from app.services.movie_service import MovieService

router = APIRouter()


@router.get("/", response_model=List[MovieResponse])
def get_movies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    genre: Optional[str] = None,
    director: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get list of movies with optional filters"""
    movies = MovieService.get_movies(
        db=db,
        skip=skip,
        limit=limit,
        genre=genre,
        director=director,
        search=search
    )
    return movies


@router.get("/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    """Get a specific movie by ID"""
    movie = MovieService.get_movie(db=db, movie_id=movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.post("/", response_model=MovieResponse, status_code=201)
def create_movie(movie: MovieCreate, db: Session = Depends(get_db)):
    """Create a new movie"""
    return MovieService.create_movie(db=db, movie=movie)


@router.put("/{movie_id}", response_model=MovieResponse)
def update_movie(
    movie_id: int,
    movie: MovieUpdate,
    db: Session = Depends(get_db)
):
    """Update a movie"""
    updated_movie = MovieService.update_movie(db=db, movie_id=movie_id, movie=movie)
    if not updated_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return updated_movie


@router.delete("/{movie_id}", status_code=204)
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    """Delete a movie"""
    success = MovieService.delete_movie(db=db, movie_id=movie_id)
    if not success:
        raise HTTPException(status_code=404, detail="Movie not found")
    return None


@router.get("/stats/total", response_model=dict)
def get_total_movies(db: Session = Depends(get_db)):
    """Get total number of movies"""
    total = MovieService.get_total_count(db=db)
    return {"total": total}