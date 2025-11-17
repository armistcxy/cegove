from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.collaborative import (
    CollaborativeRecommendationRequest,
    CollaborativeRecommendationResponse,
    HybridRecommendationRequest
)
from app.services.collaborative_service import get_cf_service
from app.services.recommendation_service import RecommendationService
from app.models.movie import Movie

router = APIRouter()

@router.post("/train")
async def train_model(db: Session = Depends(get_db)):
    """
    Train collaborative filtering model với dữ liệu hiện tại
    """
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

@router.post("/recommendations", response_model=List[CollaborativeRecommendationResponse])
async def get_collaborative_recommendations(
    request: CollaborativeRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Lấy movie recommendations cho user dựa trên collaborative filtering
    Tự động fallback sang popularity-based nếu user cold-start
    """
    cf_service = get_cf_service()
    
    # Kiểm tra nếu model chưa được train
    if cf_service.user_factors is None:
        raise HTTPException(
            status_code=400,
            detail="Model chưa được train. Vui lòng gọi /train trước."
        )
    
    # Check cold-start user
    is_cold_start = cf_service.is_cold_start_user(request.user_id, db)
    
    if is_cold_start:
        # Fallback to popularity-based recommendations
        rec_service = RecommendationService(db)
        popular_movies = rec_service.get_popular_movies(limit=request.top_n)
        
        results = []
        for movie in popular_movies:
            results.append(
                CollaborativeRecommendationResponse(
                    movie_id=movie.id,
                    predicted_score=0.0,
                    title=movie.title,
                    recommendation_type="popularity",
                    reason="User mới - đề xuất phim phổ biến"
                )
            )
        return results
    
    # Lấy collaborative recommendations
    recommendations = cf_service.recommend(
        user_id=request.user_id,
        top_n=request.top_n,
        exclude_watched=True,
        db=db
    )
    
    if not recommendations:
        # Fallback nếu không có recommendations
        rec_service = RecommendationService(db)
        popular_movies = rec_service.get_popular_movies(limit=request.top_n)
        
        results = []
        for movie in popular_movies:
            results.append(
                CollaborativeRecommendationResponse(
                    movie_id=movie.id,
                    predicted_score=0.0,
                    title=movie.title,
                    recommendation_type="popularity",
                    reason="Không đủ dữ liệu collaborative"
                )
            )
        return results
    
    # Lấy thông tin movies
    movie_ids = [rec[0] for rec in recommendations]
    movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
    movie_dict = {movie.id: movie.title for movie in movies}
    
    # Format response
    results = []
    for movie_id, score in recommendations:
        results.append(
            CollaborativeRecommendationResponse(
                movie_id=movie_id,
                predicted_score=round(score, 2),
                title=movie_dict.get(movie_id, "Unknown"),
                recommendation_type="collaborative",
                reason="Dựa trên sở thích người dùng tương tự"
            )
        )
    
    return results

@router.post("/hybrid", response_model=List[CollaborativeRecommendationResponse])
async def get_hybrid_recommendations(
    request: HybridRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Hybrid recommendations: kết hợp collaborative và content-based
    """
    cf_service = get_cf_service()
    rec_service = RecommendationService(db)
    
    # Check model
    if cf_service.user_factors is None:
        raise HTTPException(
            status_code=400,
            detail="Model chưa được train."
        )
    
    is_cold_start = cf_service.is_cold_start_user(request.user_id, db)
    
    if is_cold_start:
        # 100% popularity-based
        popular_movies = rec_service.get_popular_movies(limit=request.top_n)
        results = []
        for movie in popular_movies:
            results.append(
                CollaborativeRecommendationResponse(
                    movie_id=movie.id,
                    predicted_score=0.0,
                    title=movie.title,
                    recommendation_type="popularity",
                    reason="User mới"
                )
            )
        return results
    
    # Lấy số lượng từ mỗi nguồn
    n_collaborative = int(request.top_n * request.collaborative_weight)
    n_content = request.top_n - n_collaborative
    
    results = []
    
    # Get collaborative recommendations
    if n_collaborative > 0:
        cf_recs = cf_service.recommend(
            user_id=request.user_id,
            top_n=n_collaborative,
            exclude_watched=True,
            db=db
        )
        
        movie_ids = [rec[0] for rec in cf_recs]
        movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
        movie_dict = {movie.id: movie.title for movie in movies}
        
        for movie_id, score in cf_recs:
            results.append(
                CollaborativeRecommendationResponse(
                    movie_id=movie_id,
                    predicted_score=round(score, 2),
                    title=movie_dict.get(movie_id, "Unknown"),
                    recommendation_type="collaborative",
                    reason="Dựa trên collaborative filtering"
                )
            )
    
    # Get content-based recommendations (từ service khác nếu có)
    # TODO: Implement content-based recommendations
    
    # Fill remaining với popularity nếu cần
    if len(results) < request.top_n:
        remaining = request.top_n - len(results)
        existing_ids = {r.movie_id for r in results}
        popular_movies = rec_service.get_popular_movies(limit=remaining * 2)
        
        for movie in popular_movies:
            if movie.id not in existing_ids and len(results) < request.top_n:
                results.append(
                    CollaborativeRecommendationResponse(
                        movie_id=movie.id,
                        predicted_score=0.0,
                        title=movie.title,
                        recommendation_type="popularity",
                        reason="Phim phổ biến"
                    )
                )
                existing_ids.add(movie.id)
    
    return results[:request.top_n]

@router.get("/predict/{user_id}/{movie_id}")
async def predict_score(user_id: int, movie_id: int):
    """
    Dự đoán score cho một user-movie pair cụ thể
    """
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
    """
    Lấy thông tin về model hiện tại
    """
    cf_service = get_cf_service()
    return cf_service.get_model_info()

@router.post("/model/clear-cache")
async def clear_cache():
    """
    Xóa recommendation cache
    """
    cf_service = get_cf_service()
    cf_service.clear_cache()
    return {"message": "Cache cleared successfully"}

@router.get("/user/{user_id}/status")
async def get_user_status(user_id: int, db: Session = Depends(get_db)):
    """
    Kiểm tra status của user (cold-start hay không)
    """
    cf_service = get_cf_service()
    
    if cf_service.user_factors is None:
        return {
            "user_id": user_id,
            "status": "model_not_trained",
            "is_cold_start": True
        }
    
    is_cold_start = cf_service.is_cold_start_user(user_id, db)
    
    return {
        "user_id": user_id,
        "is_cold_start": is_cold_start,
        "exists_in_model": user_id in cf_service.user_id_map,
        "recommendation_strategy": "popularity" if is_cold_start else "collaborative"
    }