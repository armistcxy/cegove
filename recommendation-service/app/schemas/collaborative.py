from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class UserBehaviorBase(BaseModel):
    user_id: int
    movie_id: int
    behavior: str
    score: float

class UserBehaviorCreate(UserBehaviorBase):
    pass

class UserBehaviorResponse(UserBehaviorBase):
    id: int
    created_at: str
    
    class Config:
        from_attributes = True

class CollaborativeRecommendationRequest(BaseModel):
    user_id: int
    top_n: int = Field(default=10, ge=1, le=100)

class CollaborativeRecommendationResponse(BaseModel):
    movie_id: int
    predicted_score: float
    title: Optional[str] = None
    recommendation_type: Literal["collaborative", "popularity", "content"] = "collaborative"
    reason: Optional[str] = None

class HybridRecommendationRequest(BaseModel):
    user_id: int
    top_n: int = Field(default=10, ge=1, le=100)
    collaborative_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    content_weight: float = Field(default=0.3, ge=0.0, le=1.0)