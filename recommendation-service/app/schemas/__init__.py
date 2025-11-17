from app.schemas.recommendation import MovieRecommendation, RecommendationResponse
from app.schemas.collaborative import (
    UserBehaviorCreate,
    UserBehaviorResponse,
    CollaborativeRecommendationRequest,
    CollaborativeRecommendationResponse
)

__all__ = [
    "RecommendationRequest",
    "RecommendationResponse",
    "UserBehaviorCreate",
    "UserBehaviorResponse",
    "CollaborativeRecommendationRequest",
    "CollaborativeRecommendationResponse"
]