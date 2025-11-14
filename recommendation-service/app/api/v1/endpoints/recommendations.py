from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.recommendation import (
    MovieRecommendation, RecommendationResponse,
    PopularMoviesParams, TopRatedParams, SimilarMoviesParams
)
from app.services.recommendation_service import RecommendationService

router = APIRouter()


@router.get("/popular", response_model=RecommendationResponse)
def get_popular_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    min_votes: int = Query(10000, ge=0, description="Minimum votes required"),
    db: Session = Depends(get_db)
):
    """
    Get popular movie recommendations
    
    Based on number of votes and IMDB rating.
    Best for new users or homepage.
    
    - **limit**: Number of movies to return (max 50)
    - **min_votes**: Minimum number of votes required (default 10,000)
    """
    results = RecommendationService.get_popular_movies(
        db=db,
        limit=limit,
        min_votes=min_votes
    )
    
    recommendations = []
    for movie, reason in results:
        rec = MovieRecommendation(
            id=movie.id,
            series_title=movie.series_title,
            released_year=movie.released_year,
            genre=movie.genre,
            imdb_rating=movie.imdb_rating,
            meta_score=movie.meta_score,
            director=movie.director,
            poster_link=movie.poster_link,
            overview=movie.overview,
            no_of_votes=movie.no_of_votes,
            reason=reason
        )
        recommendations.append(rec)
    
    return RecommendationResponse(
        recommendations=recommendations,
        total=len(recommendations),
        method="popular"
    )


@router.get("/top-rated", response_model=RecommendationResponse)
def get_top_rated_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    min_votes: int = Query(5000, ge=0, description="Minimum votes required"),
    db: Session = Depends(get_db)
):
    """
    Get top rated movie recommendations
    
    Based on highest IMDB ratings with sufficient votes.
    
    - **limit**: Number of movies to return (max 50)
    - **min_votes**: Minimum number of votes required (default 5,000)
    """
    results = RecommendationService.get_top_rated_movies(
        db=db,
        limit=limit,
        min_votes=min_votes
    )
    
    recommendations = []
    for movie, reason in results:
        rec = MovieRecommendation(
            id=movie.id,
            series_title=movie.series_title,
            released_year=movie.released_year,
            genre=movie.genre,
            imdb_rating=movie.imdb_rating,
            meta_score=movie.meta_score,
            director=movie.director,
            poster_link=movie.poster_link,
            overview=movie.overview,
            no_of_votes=movie.no_of_votes,
            reason=reason
        )
        recommendations.append(rec)
    
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
    Get similar movie recommendations (Content-Based Filtering)
    
    Uses TF-IDF on movie features:
    - Genre (weighted heavily)
    - Director (weighted)
    - Overview/plot
    - Cast members
    
    Returns movies with similar content and style.
    
    - **movie_id**: Source movie ID
    - **limit**: Number of recommendations (max 50)
    """
    source_movie, results = RecommendationService.get_similar_movies_content_based(
        db=db,
        movie_id=movie_id,
        limit=limit
    )
    
    if not source_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    if not results:
        # Fallback: Get movies by same genre
        if source_movie.genre:
            genre = source_movie.genre.split(',')[0].strip()
            fallback_results = RecommendationService.get_movies_by_genre(
                db=db,
                genre=genre,
                limit=limit,
                exclude_movie_id=movie_id
            )
            
            recommendations = []
            for movie, reason in fallback_results:
                rec = MovieRecommendation(
                    id=movie.id,
                    series_title=movie.series_title,
                    released_year=movie.released_year,
                    genre=movie.genre,
                    imdb_rating=movie.imdb_rating,
                    meta_score=movie.meta_score,
                    director=movie.director,
                    poster_link=movie.poster_link,
                    overview=movie.overview,
                    no_of_votes=movie.no_of_votes,
                    similarity_score=None,
                    reason=reason
                )
                recommendations.append(rec)
            
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
                detail="No similar movies found and no genre available for fallback"
            )
    
    recommendations = []
    for movie, similarity, reason in results:
        rec = MovieRecommendation(
            id=movie.id,
            series_title=movie.series_title,
            released_year=movie.released_year,
            genre=movie.genre,
            imdb_rating=movie.imdb_rating,
            meta_score=movie.meta_score,
            director=movie.director,
            poster_link=movie.poster_link,
            overview=movie.overview,
            no_of_votes=movie.no_of_votes,
            similarity_score=round(similarity, 4),
            reason=reason
        )
        recommendations.append(rec)
    
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
    Get movie recommendations by genre
    
    Simple genre-based recommendations sorted by rating.
    
    - **genre**: Genre name (e.g., "Action", "Drama")
    - **limit**: Number of movies (max 50)
    """
    results = RecommendationService.get_movies_by_genre(
        db=db,
        genre=genre,
        limit=limit
    )
    
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No movies found for genre: {genre}"
        )
    
    recommendations = []
    for movie, reason in results:
        rec = MovieRecommendation(
            id=movie.id,
            series_title=movie.series_title,
            released_year=movie.released_year,
            genre=movie.genre,
            imdb_rating=movie.imdb_rating,
            meta_score=movie.meta_score,
            director=movie.director,
            poster_link=movie.poster_link,
            overview=movie.overview,
            no_of_votes=movie.no_of_votes,
            reason=reason
        )
        recommendations.append(rec)
    
    return RecommendationResponse(
        recommendations=recommendations,
        total=len(recommendations),
        method="genre-based",
        based_on_movie_title=genre
    )