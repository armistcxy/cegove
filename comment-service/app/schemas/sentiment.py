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


# ==================== AI INSIGHTS SCHEMAS ====================

class AIInsightResponse(BaseModel):
    """AI-generated insights about a target"""
    target_type: Literal["movie", "theater"]
    target_id: int
    
    # AI insights
    summary: str = Field(..., description="2-3 câu tóm tắt tổng quan")
    positive_aspects: List[str] = Field(..., description="Những điểm được khen nhiều")
    negative_aspects: List[str] = Field(..., description="Những điểm bị chê nhiều")
    recommendations: str = Field(..., description="Gợi ý cho người xem")
    
    # Metadata
    based_on_comments: int
    model_used: str
    generated_at: datetime
    is_stale: bool
    
    class Config:
        from_attributes = True


class CombinedInsightResponse(BaseModel):
    """Combined sentiment score + AI insights"""
    # Sentiment data
    sentiment_score: TargetSentimentScore
    
    # AI insights
    ai_insight: Optional[AIInsightResponse] = None
    
    class Config:
        from_attributes = True


# ==================== TEST AI INSIGHTS ====================

class TestAIInsightRequest(BaseModel):
    """Request to test AI insights with custom comments"""
    comments: List[str] = Field(
        ..., 
        min_length=3, 
        max_length=100,
        description="Danh sách các bình luận để phân tích (tối thiểu 3, tối đa 100)"
    )
    context: Optional[str] = Field(
        None,
        description="Ngữ cảnh: 'movie' hoặc 'theater' (tùy chọn, để tùy chỉnh prompt)"
    )


class TestAIInsightResponse(BaseModel):
    """Response from test AI insights"""
    # Input
    total_comments_analyzed: int
    
    # Sentiment analysis
    sentiment_distribution: dict = Field(
        ...,
        description="Phân bố sentiment: {positive: int, neutral: int, negative: int}"
    )
    average_sentiment_score: float = Field(..., ge=0, le=5)
    
    # AI insights
    summary: str = Field(..., description="Tóm tắt tổng quan")
    positive_aspects: List[str] = Field(..., description="Xu hướng khen")
    negative_aspects: List[str] = Field(..., description="Xu hướng chê")
    recommendations: str = Field(..., description="Gợi ý cho người xem")
    
    # Metadata
    model_used: str
    processing_time_seconds: float