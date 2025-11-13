from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.models.movie import Movie
from app.schemas.movie import MovieCreate, MovieUpdate


class MovieService:
    
    @staticmethod
    def get_movies(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        genre: Optional[str] = None,
        director: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Movie]:
        query = db.query(Movie)
        
        if genre:
            query = query.filter(Movie.genre.ilike(f"%{genre}%"))
        
        if director:
            query = query.filter(Movie.director.ilike(f"%{director}%"))
        
        if search:
            query = query.filter(
                or_(
                    Movie.series_title.ilike(f"%{search}%"),
                    Movie.overview.ilike(f"%{search}%")
                )
            )
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_movie(db: Session, movie_id: int) -> Optional[Movie]:
        return db.query(Movie).filter(Movie.id == movie_id).first()
    
    @staticmethod
    def create_movie(db: Session, movie: MovieCreate) -> Movie:
        db_movie = Movie(**movie.model_dump())
        db.add(db_movie)
        db.commit()
        db.refresh(db_movie)
        return db_movie
    
    @staticmethod
    def update_movie(
        db: Session,
        movie_id: int,
        movie: MovieUpdate
    ) -> Optional[Movie]:
        db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if not db_movie:
            return None
        
        update_data = movie.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_movie, field, value)
        
        db.commit()
        db.refresh(db_movie)
        return db_movie
    
    @staticmethod
    def delete_movie(db: Session, movie_id: int) -> bool:
        db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if not db_movie:
            return False
        
        db.delete(db_movie)
        db.commit()
        return True
    
    @staticmethod
    def get_total_count(db: Session) -> int:
        return db.query(Movie).count()