from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.collaborative import (
    CollaborativeRecommendationRequest,
    CollaborativeRecommendationResponse
)
from app.services.collaborative_service import get_cf_service
from app.models.movie import Movie

router = APIRouter()

@router.post("/train")
async def train_model(db: Session = Depends(get_db)):
    """
    Train collaborative filtering model với dữ liệu hiện tại
    """
    try:
        cf_service = get_cf_service()
        cf_service.train(db)
        return {
            "message": "Model trained successfully",
            "n_users": len(cf_service.user_id_map),
            "n_movies": len(cf_service.movie_id_map)
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
    """
    cf_service = get_cf_service()
    
    # Kiểm tra nếu model chưa được train
    if cf_service.user_factors is None:
        raise HTTPException(
            status_code=400, 
            detail="Model chưa được train. Vui lòng gọi /train trước."
        )
    
    # Lấy recommendations
    recommendations = cf_service.recommend(
        user_id=request.user_id,
        top_n=request.top_n,
        exclude_watched=True,
        db=db
    )
    
    if not recommendations:
        return []
    
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
                title=movie_dict.get(movie_id, "Unknown")
            )
        )
    
    return results

@router.get("/predict/{user_id}/{movie_id}")
async def predict_score(user_id: int, movie_id: int):
    """
    Dự đoán score cho một user-movie pair cụ thể
    """
    cf_service = get_cf_service()
    
    if cf_service.user_factors is None:
        raise HTTPException(
            status_code=400,
            detail="Model chưa được train. Vui lòng gọi /train trước."
        )
    
    score = cf_service.predict(user_id, movie_id)
    
    return {
        "user_id": user_id,
        "movie_id": movie_id,
        "predicted_score": round(score, 2)
    }