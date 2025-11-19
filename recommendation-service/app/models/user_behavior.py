from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base

class UserBehavior(Base):
    __tablename__ = "user_behaviors"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    movie_id = Column(Integer, index=True, nullable=False)
    behavior = Column(String(50), nullable=False)  # view, like, rate, watch_complete
    score = Column(Float, nullable=False)  # điểm tương ứng với behavior
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<UserBehavior(user_id={self.user_id}, movie_id={self.movie_id}, behavior={self.behavior})>"