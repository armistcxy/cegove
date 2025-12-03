from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from datetime import datetime


class SentimentPrediction(BaseModel):
    """Raw sentiment prediction result"""
    negative: float = Field(..., ge=0, le=1)
    positive: float = Field(..., ge=0, le=1)
    neutral: float = Field(..., ge=0, le=1)
    score: float = Field(..., ge=0, le=5, description="Sentiment score 0-5")
    label: Literal["positive", "neutral", "negative"]
    processed_text: Optional[str] = None


class CommentSentimentResponse(BaseModel):
    """Comment with sentiment analysis"""
    comment_id: int
    sentiment: SentimentPrediction
    created_at: datetime
    
    class Config:
        from_attributes = True


class TargetSentimentScore(BaseModel):
    """Overall sentiment score for a target"""
    target_type: Literal["movie", "theater"]
    target_id: int
    average_score: float = Field(..., ge=0, le=5)
    total_comments: int
    positive_count: int
    neutral_count: int
    negative_count: int
    avg_positive_prob: float
    avg_neutral_prob: float
    avg_negative_prob: float
    last_calculated_at: datetime
    is_stale: bool
    
    class Config:
        from_attributes = True


class SentimentDistribution(BaseModel):
    """Sentiment distribution visualization data"""
    positive_percentage: float
    neutral_percentage: float
    negative_percentage: float
    score_histogram: List[int] = Field(..., description="Count for each score 0-5")


class TextProcessRequest(BaseModel):
    """Request to test text processing"""
    text: str = Field(..., min_length=1, max_length=2000)


class TextProcessResponse(BaseModel):
    """Response from text processing"""
    original_text: str
    normalized_text: str
    segmented_text: str


class BatchSentimentRequest(BaseModel):
    """Request to analyze multiple texts"""
    texts: List[str] = Field(..., min_length=1, max_length=100)


class BatchSentimentResponse(BaseModel):
    """Response from batch sentiment analysis"""
    results: List[SentimentPrediction]
    total_processed: int