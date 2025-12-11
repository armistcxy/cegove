from typing import List, Set, Tuple
from sqlalchemy.orm import Session
from app.models.movie import Movie
from app.schemas.recommendation import MovieRecommendation


def fill_with_popular_movies(
    db: Session,
    existing_recommendations: List[MovieRecommendation],
    target_count: int,
    exclude_movie_ids: Set[int],
    rec_service
) -> List[MovieRecommendation]:
    """
    Fill remaining slots with popular movies
    
    Args:
        db: Database session
        existing_recommendations: Current recommendations list
        target_count: Target number of recommendations
        exclude_movie_ids: Set of movie IDs to exclude
        rec_service: RecommendationService instance
        
    Returns:
        Updated recommendations list with popular movies added
    """
    if len(existing_recommendations) >= target_count:
        return existing_recommendations[:target_count]
    
    remaining = target_count - len(existing_recommendations)
    popular_movies = rec_service.get_popular_movies(limit=remaining * 2)
    
    results = existing_recommendations.copy()
    
    for movie in popular_movies:
        if movie.id not in exclude_movie_ids and len(results) < target_count:
            results.append(
                MovieRecommendation(
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
                    predicted_score=0.0,
                    recommendation_type="popularity",
                    reason="Phim phổ biến"
                )
            )
            exclude_movie_ids.add(movie.id)
    
    return results[:target_count]


def movie_to_recommendation(
    movie: Movie,
    predicted_score: float = 0.0,
    recommendation_type: str = "popularity",
    reason: str = None
) -> MovieRecommendation:
    """Convert Movie model to MovieRecommendation schema"""
    return MovieRecommendation(
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
        predicted_score=predicted_score,
        recommendation_type=recommendation_type,
        reason=reason
    )


def get_user_watched_movies(db: Session, user_id: int) -> Tuple[List, Set[int]]:
    """
    Get user's watched movies and their IDs
    
    Returns:
        Tuple of (user_ratings_list, watched_movie_ids_set)
    """
    from app.models.rating import Rating
    user_ratings = db.query(Rating).filter(Rating.user_id == user_id).all()
    watched_movie_ids = {r.movie_id for r in user_ratings}
    return user_ratings, watched_movie_ids


def get_content_based_from_user_history(
    db: Session,
    user_ratings: List,
    watched_movie_ids: Set[int],
    top_n: int,
    rec_service,
    num_source_movies: int = 5
) -> List[Tuple]:
    """
    Get content-based recommendations from user's top rated movies
    
    Returns:
        List of tuples (movie, similarity, reason, source_title)
    """
    if not user_ratings:
        return []
    
    top_rated = sorted(user_ratings, key=lambda x: x.rating, reverse=True)[:num_source_movies]
    content_based_results = []
    seen_movie_ids = set()
    
    for rating in top_rated:
        source_movie, similar_movies = rec_service.get_similar_movies_content_based(
            db=db,
            movie_id=rating.movie_id,
            limit=top_n * 2
        )
        
        if similar_movies:
            for movie, similarity, reason in similar_movies:
                if movie.id not in watched_movie_ids and movie.id not in seen_movie_ids:
                    content_based_results.append((movie, similarity, reason, source_movie.series_title))
                    seen_movie_ids.add(movie.id)
    
    # Sort by similarity
    content_based_results.sort(key=lambda x: x[1], reverse=True)
    return content_based_results