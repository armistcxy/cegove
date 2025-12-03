from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base


class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Polymorphic - có thể comment cho movie hoặc theater
    target_type = Column(String(20), nullable=False, index=True)  # 'movie' hoặc 'theater'
    target_id = Column(Integer, nullable=False, index=True)
    
    # Content
    content = Column(Text, nullable=False)
    rating = Column(Float, nullable=True)  # Rating 1-5, optional
    
    # Metadata
    user_name = Column(String(255), nullable=True)  # Cache user name
    user_email = Column(String(255), nullable=True)  # Cache user email
    
    # Moderation
    is_approved = Column(Boolean, default=True)
    is_flagged = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Comment(id={self.id}, user_id={self.user_id}, target_type={self.target_type}, target_id={self.target_id})>"


# Composite indexes for performance
Index('ix_comments_target', Comment.target_type, Comment.target_id)
Index('ix_comments_user_target', Comment.user_id, Comment.target_type, Comment.target_id)


class CommentLike(Base):
    __tablename__ = "comment_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey('comments.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<CommentLike(comment_id={self.comment_id}, user_id={self.user_id})>"


# Unique constraint: một user chỉ like một comment một lần
Index('ix_comment_likes_unique', CommentLike.comment_id, CommentLike.user_id, unique=True)


class CommentReport(Base):
    __tablename__ = "comment_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey('comments.id', ondelete='CASCADE'), nullable=False, index=True)
    reporter_user_id = Column(Integer, nullable=False, index=True)
    reason = Column(String(50), nullable=False)  # spam, inappropriate, offensive, etc.
    description = Column(Text, nullable=True)
    status = Column(String(20), default='pending', index=True)  # pending, reviewed, resolved
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<CommentReport(comment_id={self.comment_id}, reason={self.reason}, status={self.status})>"