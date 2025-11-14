from pydantic import BaseModel
from typing import List, Optional

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
    top_n: int = 10

class CollaborativeRecommendationResponse(BaseModel):
    movie_id: int
    predicted_score: float
    title: Optional[str] = None