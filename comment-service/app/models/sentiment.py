from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Index
from sqlalchemy.sql import func
from app.database import Base


class SentimentScore(Base):
    """Cached sentiment scores for targets (movies/theaters)"""
    __tablename__ = "sentiment_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String(20), nullable=False, index=True)  # 'movie' or 'theater'
    target_id = Column(Integer, nullable=False, index=True)
    
    # Sentiment scores
    average_score = Column(Float, nullable=False)  # 0-5 scale
    total_comments = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    
    # Raw probabilities (average across all comments)
    avg_positive_prob = Column(Float, default=0.0)
    avg_neutral_prob = Column(Float, default=0.0)
    avg_negative_prob = Column(Float, default=0.0)
    
    # Metadata
    last_calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    is_stale = Column(Boolean, default=False)  # True if new comments added
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# Unique index for target
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
    sentiment_label = Column(String(10), nullable=False)  # 'positive', 'neutral', 'negative'
    
    # Preprocessed text (for debugging)
    processed_text = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())