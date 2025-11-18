from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.recommendation import (
    MovieRecommendation, 
    RecommendationResponse,
    RecommendationRequest,
    ContentBasedRequest
)
from app.services.recommendation_service import RecommendationService
from app.services.recommendation_helpers import movie_to_recommendation

router = APIRouter()


@router.get("/popular", response_model=RecommendationResponse)
def get_popular_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    min_votes: int = Query(10000, ge=0, description="Minimum votes required"),
    db: Session = Depends(get_db)
):
    """
    Get popular movie recommendations based on votes and rating
    Best for new users or homepage
    """
    rec_service = RecommendationService(db)
    results = rec_service.get_popular_movies(limit=limit, min_votes=min_votes)
    
    recommendations = [
        movie_to_recommendation(
            movie=movie,
            recommendation_type="popularity",
            reason=reason
        )
        for movie, reason in results
    ]
    
    return RecommendationResponse(
        recommendations=recommendations,
        total=len(recommendations),
        method="popularity"
    )


@router.get("/top-rated", response_model=RecommendationResponse)
def get_top_rated_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    min_votes: int = Query(5000, ge=0, description="Minimum votes required"),
    db: Session = Depends(get_db)
):
    """
    Get top rated movie recommendations based on IMDB ratings
    """
    rec_service = RecommendationService(db)
    results = rec_service.get_top_rated_movies(limit=limit, min_votes=min_votes)
    
    recommendations = [
        movie_to_recommendation(
            movie=movie,
            recommendation_type="popularity",
            reason=reason
        )
        for movie, reason in results
    ]
    
    return RecommendationResponse(
        recommendations=recommendations,
        total=len(recommendations),
        method="top-rated"
    )


@router.get("/similar/{movie_id}", response_model=RecommendationResponse)
def get_similar_movie_recommendations(
    movie_id: int,
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    db: Session = Depends(get_db)
):
    """
    Get similar movie recommendations using Content-Based Filtering (TF-IDF)
    
    Uses features: genre, director, overview, cast
    """
    rec_service = RecommendationService(db)
    source_movie, results = rec_service.get_similar_movies_content_based(
        db=db,
        movie_id=movie_id,
        limit=limit
    )
    
    if not source_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    if not results:
        # Fallback: same genre
        if source_movie.genre:
            genre = source_movie.genre.split(',')[0].strip()
            fallback_results = rec_service.get_movies_by_genre(
                db=db,
                genre=genre,
                limit=limit,
                exclude_movie_id=movie_id
            )
            
            recommendations = [
                movie_to_recommendation(
                    movie=movie,
                    recommendation_type="content-based",
                    reason=reason
                )
                for movie, reason in fallback_results
            ]
            
            return RecommendationResponse(
                recommendations=recommendations,
                total=len(recommendations),
                method="content-based-fallback",
                based_on_movie_id=movie_id,
                based_on_movie_title=source_movie.series_title
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="No similar movies found"
            )
    
    recommendations = [
        movie_to_recommendation(
            movie=movie,
            predicted_score=round(similarity, 4),
            recommendation_type="content-based",
            reason=reason
        )
        for movie, similarity, reason in results
    ]
    
    return RecommendationResponse(
        recommendations=recommendations,
        total=len(recommendations),
        method="content-based",
        based_on_movie_id=movie_id,
        based_on_movie_title=source_movie.series_title
    )


@router.get("/by-genre/{genre}", response_model=RecommendationResponse)
def get_recommendations_by_genre(
    genre: str,
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    db: Session = Depends(get_db)
):
    """
    Get movie recommendations by genre, sorted by rating
    """
    rec_service = RecommendationService(db)
    results = rec_service.get_movies_by_genre(db=db, genre=genre, limit=limit)
    
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No movies found for genre: {genre}"
        )
    
    recommendations = [
        movie_to_recommendation(
            movie=movie,
            recommendation_type="content-based",
            reason=reason
        )
        for movie, reason in results
    ]
    
    return RecommendationResponse(
        recommendations=recommendations,
        total=len(recommendations),
        method="genre-based",
        based_on_movie_title=genre
    )