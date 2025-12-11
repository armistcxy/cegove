# comment-service/app/schemas/comment.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal, Dict
from datetime import datetime


class CommentBase(BaseModel):
    target_type: Literal["movie", "theater"] = Field(..., description="Type of target: movie or theater")
    target_id: int = Field(..., gt=0, description="ID of movie or theater")
    content: str = Field(..., min_length=1, max_length=2000, description="Comment content")
    rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Rating from 1 to 5 stars")


class CommentCreate(CommentBase):
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()
    
    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if v is not None and (v < 1.0 or v > 5.0):
            raise ValueError('Rating must be between 1.0 and 5.0')
        return v


class CommentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Rating from 1 to 5 stars")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Content cannot be empty')
        return v.strip() if v else v
    
    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if v is not None and (v < 1.0 or v > 5.0):
            raise ValueError('Rating must be between 1.0 and 5.0')
        return v


class CommentResponse(CommentBase):
    id: int
    user_id: int
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    rating: Optional[float] = None
    is_approved: bool
    is_flagged: bool
    created_at: datetime
    updated_at: datetime
    
    # Aggregated data (computed)
    likes_count: int = 0
    user_has_liked: bool = False
    
    class Config:
        from_attributes = True


class CommentWithStats(CommentResponse):
    """Comment with additional statistics"""
    reports_count: int = 0


class PaginatedCommentsResponse(BaseModel):
    items: List[CommentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class CommentLikeResponse(BaseModel):
    id: int
    comment_id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CommentReportCreate(BaseModel):
    reason: Literal["spam", "inappropriate", "offensive", "misleading", "other"] = Field(
        ..., description="Reason for reporting"
    )
    description: Optional[str] = Field(None, max_length=500, description="Additional details")


class CommentReportResponse(BaseModel):
    id: int
    comment_id: int
    reporter_user_id: int
    reason: str
    description: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class CommentStatistics(BaseModel):
    """Statistics for comments on a specific target"""
    target_type: str
    target_id: int
    total_comments: int
    total_likes: int
    recent_comments_count: int  # Last 7 days
    average_rating: Optional[float] = Field(None, description="Average rating (1-5)")
    total_ratings: int = Field(0, description="Number of comments with ratings")
    rating_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Distribution of ratings: {'1': count, '2': count, ...}"
    )


class CommentModerationUpdate(BaseModel):
    is_approved: Optional[bool] = None
    is_flagged: Optional[bool] = None


class BulkCommentAction(BaseModel):
    comment_ids: List[int] = Field(..., min_length=1, max_length=100)
    action: Literal["approve", "flag", "delete"] = Field(..., description="Action to perform")


class SentimentAnalysisResult(BaseModel):
    """Future use: sentiment analysis result"""
    target_type: str
    target_id: int
    positive_count: int
    negative_count: int
    neutral_count: int
    average_sentiment_score: float
    keywords: List[str]
    date_range: str