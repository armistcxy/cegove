from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base


class SentimentScore(Base):
    """Cached sentiment scores for targets (movies/theaters)"""
    __tablename__ = "sentiment_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String(20), nullable=False, index=True)
    target_id = Column(Integer, nullable=False, index=True)
    
    # Sentiment scores
    average_score = Column(Float, nullable=False)
    total_comments = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    
    # Raw probabilities
    avg_positive_prob = Column(Float, default=0.0)
    avg_neutral_prob = Column(Float, default=0.0)
    avg_negative_prob = Column(Float, default=0.0)
    
    # Metadata
    last_calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    is_stale = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


Index('ix_sentiment_target_unique', SentimentScore.target_type, SentimentScore.target_id, unique=True)


class CommentSentiment(Base):
    """Individual comment sentiment cache"""
    __tablename__ = "comment_sentiments"
    
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, nullable=False, unique=True, index=True)
    
    # Sentiment probabilities
    positive_prob = Column(Float, nullable=False)
    neutral_prob = Column(Float, nullable=False)
    negative_prob = Column(Float, nullable=False)
    
    # Calculated score (0-5)
    sentiment_score = Column(Float, nullable=False)
    sentiment_label = Column(String(10), nullable=False)
    
    # Preprocessed text
    processed_text = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ==================== AI INSIGHTS ====================

class AIInsight(Base):
    """AI-generated insights from comments"""
    __tablename__ = "ai_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String(20), nullable=False, index=True)
    target_id = Column(Integer, nullable=False, index=True)
    
    # AI-generated content
    summary = Column(Text, nullable=False)  # Tóm tắt tổng quan
    positive_aspects = Column(Text, nullable=False)  # Xu hướng khen (JSON array)
    negative_aspects = Column(Text, nullable=False)  # Xu hướng chê (JSON array)
    recommendations = Column(Text, nullable=False)  # Gợi ý cho người xem
    
    # Metadata
    based_on_comments = Column(Integer, default=0)  # Số comments được phân tích
    model_used = Column(String(50), default="gemini-pro")
    is_stale = Column(Boolean, default=False)
    
    # Timestamps
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


Index('ix_ai_insights_target_unique', AIInsight.target_type, AIInsight.target_id, unique=True)