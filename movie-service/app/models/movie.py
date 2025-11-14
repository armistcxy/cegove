from sqlalchemy import Column, Integer, String, Float, Text, BigInteger, Index
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.dialects.postgresql import TSVECTOR
from app.database import Base


class Movie(Base):
    __tablename__ = "movies"
    
    id = Column(Integer, primary_key=True, index=True)
    poster_link = Column(String(500), nullable=True)
    series_title = Column(String(255), nullable=False, index=True)
    released_year = Column(String(10), nullable=True, index=True)
    certificate = Column(String(50), nullable=True)
    runtime = Column(String(50), nullable=True)
    genre = Column(String(255), nullable=True, index=True)
    imdb_rating = Column(Float, nullable=True, index=True)
    overview = Column(Text, nullable=True)
    meta_score = Column(Integer, nullable=True, index=True)
    director = Column(String(255), nullable=True, index=True)
    star1 = Column(String(255), nullable=True)
    star2 = Column(String(255), nullable=True)
    star3 = Column(String(255), nullable=True)
    star4 = Column(String(255), nullable=True)
    no_of_votes = Column(BigInteger, nullable=True)
    gross = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Full-text search vector (computed column)
    # search_vector = Column(TSVECTOR)
    
    def __repr__(self):
        return f"<Movie(id={self.id}, title='{self.series_title}', year={self.released_year})>"


# Create GIN index for full-text search
# This will be created via migration or database.py
Index(
    'ix_movies_search',
    func.to_tsvector('english', 
        func.coalesce(Movie.series_title, '') + ' ' +
        func.coalesce(Movie.overview, '') + ' ' +
        func.coalesce(Movie.director, '') + ' ' +
        func.coalesce(Movie.genre, '')
    ),
    postgresql_using='gin'
)