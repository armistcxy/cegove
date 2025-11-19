from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    CollaborativeRequest,
    MovieRecommendation
)
from app.services.collaborative_service import get_cf_service
from app.services.recommendation_service import RecommendationService
from app.services.recommendation_helpers import (
    fill_with_popular_movies,
    movie_to_recommendation,
    get_user_watched_movies,
    get_content_based_from_user_history
)
from app.models.movie import Movie

router = APIRouter()


@router.post("/train")
async def train_model(db: Session = Depends(get_db)):
    """Train collaborative filtering model with current data"""
    try:
        cf_service = get_cf_service()
        result = cf_service.train(db, verbose=True)
        return {
            "message": "Model trained successfully",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.post("/recommendations", response_model=RecommendationResponse)
async def get_collaborative_recommendations(
    request: CollaborativeRequest,
    db: Session = Depends(get_db)
):
    """
    Get pure collaborative filtering recommendations
    Auto fallback to popularity if cold-start user
    """
    cf_service = get_cf_service()
    rec_service = RecommendationService(db)
    
    if cf_service.user_factors is None:
        raise HTTPException(
            status_code=400,
            detail="Model chưa được train. Vui lòng gọi /train trước."
        )
    
    is_cold_start = cf_service.is_cold_start_user(request.user_id, db)
    
    if is_cold_start:
        popular_movies = rec_service.get_popular_movies(limit=request.top_n)
        recommendations = [
            movie_to_recommendation(
                movie=movie,
                recommendation_type="popularity",
                reason="User mới - đề xuất phim phổ biến"
            )
            for movie, _ in popular_movies
        ]
        
        return RecommendationResponse(
            recommendations=recommendations,
            total=len(recommendations),
            method="collaborative-fallback-popularity",
            user_id=request.user_id,
            is_cold_start=True
        )
    
    # Get collaborative recommendations
    cf_recommendations = cf_service.recommend(
        user_id=request.user_id,
        top_n=request.top_n,
        exclude_watched=True,
        db=db
    )
    
    if not cf_recommendations:
        popular_movies = rec_service.get_popular_movies(limit=request.top_n)
        recommendations = [
            movie_to_recommendation(
                movie=movie,
                recommendation_type="popularity",
                reason="Không đủ dữ liệu collaborative"
            )
            for movie, _ in popular_movies
        ]
        
        return RecommendationResponse(
            recommendations=recommendations,
            total=len(recommendations),
            method="collaborative-fallback-popularity",
            user_id=request.user_id,
            is_cold_start=False
        )
    
    # Get movie details
    movie_ids = [rec[0] for rec in cf_recommendations]
    movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
    movie_dict = {movie.id: movie for movie in movies}
    
    recommendations = [
        movie_to_recommendation(
            movie=movie_dict[movie_id],
            predicted_score=round(score, 2),
            recommendation_type="collaborative",
            reason="Dựa trên sở thích người dùng tương tự"
        )
        for movie_id, score in cf_recommendations
        if movie_id in movie_dict
    ]
    
    return RecommendationResponse(
        recommendations=recommendations,
        total=len(recommendations),
        method="collaborative",
        user_id=request.user_id,
        is_cold_start=False
    )


@router.post("/personalized", response_model=RecommendationResponse)
async def get_personalized_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Personalized hybrid recommendations: collaborative + content-based
    - Cold-start users: 100% content-based (from watched movies)
    - Regular users: Hybrid weighted combination
    """
    cf_service = get_cf_service()
    rec_service = RecommendationService(db)
    
    if cf_service.user_factors is None:
        raise HTTPException(
            status_code=400,
            detail="Model chưa được train. Vui lòng gọi /train trước."
        )
    
    is_cold_start = cf_service.is_cold_start_user(request.user_id, db)
    user_ratings, watched_movie_ids = get_user_watched_movies(db, request.user_id)
    
    # --- Cold-start user: 100% content-based ---
    if is_cold_start:
        if not user_ratings:
            # No ratings at all -> popularity
            popular_movies = rec_service.get_popular_movies(limit=request.top_n)
            recommendations = [
                movie_to_recommendation(
                    movie=movie,
                    recommendation_type="popularity",
                    reason="User mới - đề xuất phim phổ biến"
                )
                for movie, _ in popular_movies
            ]
            
            return RecommendationResponse(
                recommendations=recommendations,
                total=len(recommendations),
                method="personalized-cold-start-popularity",
                user_id=request.user_id,
                is_cold_start=True
            )
        
        # Content-based from top rated movies
        content_based_results = get_content_based_from_user_history(
            db=db,
            user_ratings=user_ratings,
            watched_movie_ids=watched_movie_ids,
            top_n=request.top_n,
            rec_service=rec_service,
            num_source_movies=3
        )
        
        recommendations = [
            movie_to_recommendation(
                movie=movie,
                predicted_score=round(similarity, 2),
                recommendation_type="content-based",
                reason=f"Tương tự với '{source_title}' mà bạn đã xem"
            )
            for movie, similarity, _, source_title in content_based_results[:request.top_n]
        ]
        
        # Fill with popularity if needed
        existing_ids = watched_movie_ids | {r.id for r in recommendations}
        recommendations = fill_with_popular_movies(
            db=db,
            existing_recommendations=recommendations,
            target_count=request.top_n,
            exclude_movie_ids=existing_ids,
            rec_service=rec_service
        )
        
        return RecommendationResponse(
            recommendations=recommendations,
            total=len(recommendations),
            method="personalized-cold-start-content",
            user_id=request.user_id,
            is_cold_start=True
        )
    
    # --- Regular user: Hybrid collaborative + content-based ---
    # Validate and adjust weights
    weight = max(0.0, min(1.0, request.collaborative_weight))
    n_collaborative = int(request.top_n * weight)
    n_content = request.top_n - n_collaborative
    
    recommendations = []
    existing_ids = watched_movie_ids.copy()
    
    # 1. Collaborative recommendations
    if n_collaborative > 0:
        cf_recs = cf_service.recommend(
            user_id=request.user_id,
            top_n=n_collaborative,
            exclude_watched=True,
            db=db
        )
        
        if cf_recs:
            movie_ids = [rec[0] for rec in cf_recs]
            movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
            movie_dict = {movie.id: movie for movie in movies}
            
            for movie_id, score in cf_recs:
                if movie_id in movie_dict:
                    recommendations.append(
                        movie_to_recommendation(
                            movie=movie_dict[movie_id],
                            predicted_score=round(score, 2),
                            recommendation_type="collaborative",
                            reason="Dựa trên người dùng tương tự"
                        )
                    )
                    existing_ids.add(movie_id)
    
    # 2. Content-based recommendations
    if n_content > 0:
        content_based_results = get_content_based_from_user_history(
            db=db,
            user_ratings=user_ratings,
            watched_movie_ids=existing_ids,
            top_n=n_content,
            rec_service=rec_service,
            num_source_movies=5
        )
        
        added_content = 0
        for movie, similarity, _, source_title in content_based_results:
            if added_content >= n_content:
                break
            if movie.id not in existing_ids:
                recommendations.append(
                    movie_to_recommendation(
                        movie=movie,
                        predicted_score=round(similarity, 2),
                        recommendation_type="content-based",
                        reason=f"Tương tự '{source_title}'"
                    )
                )
                existing_ids.add(movie.id)
                added_content += 1
    
    # 3. Fill with popularity if needed
    recommendations = fill_with_popular_movies(
        db=db,
        existing_recommendations=recommendations,
        target_count=request.top_n,
        exclude_movie_ids=existing_ids,
        rec_service=rec_service
    )
    
    return RecommendationResponse(
        recommendations=recommendations,
        total=len(recommendations),
        method="personalized-hybrid",
        user_id=request.user_id,
        is_cold_start=False
    )


@router.get("/predict/{user_id}/{movie_id}")
async def predict_score(user_id: int, movie_id: int):
    """Predict rating score for a specific user-movie pair"""
    cf_service = get_cf_service()
    
    if cf_service.user_factors is None:
        raise HTTPException(
            status_code=400,
            detail="Model chưa được train."
        )
    
    score = cf_service.predict(user_id, movie_id)
    
    return {
        "user_id": user_id,
        "movie_id": movie_id,
        "predicted_score": round(score, 2)
    }


@router.get("/model/info")
async def get_model_info():
    """Get current model information and statistics"""
    cf_service = get_cf_service()
    return cf_service.get_model_info()


@router.post("/model/clear-cache")
async def clear_cache():
    """Clear recommendation cache"""
    cf_service = get_cf_service()
    cf_service.clear_cache()
    return {"message": "Cache cleared successfully"}


@router.get("/user/{user_id}/status")
async def get_user_status(user_id: int, db: Session = Depends(get_db)):
    """Check user status (cold-start or not)"""
    cf_service = get_cf_service()
    
    if cf_service.user_factors is None:
        return {
            "user_id": user_id,
            "status": "model_not_trained",
            "is_cold_start": True,
            "recommendation_strategy": "popularity"
        }
    
    is_cold_start = cf_service.is_cold_start_user(user_id, db)
    
    return {
        "user_id": user_id,
        "is_cold_start": is_cold_start,
        "exists_in_model": user_id in cf_service.user_id_map,
        "recommendation_strategy": "content-based" if is_cold_start else "hybrid"
    }