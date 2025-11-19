from sqlalchemy.orm import Session
from sqlalchemy import or_, func, desc, asc, case, and_
from typing import List, Optional, Tuple, Dict
from app.models.movie import Movie
from app.schemas.movie import MovieCreate, MovieUpdate, PaginationParams


class MovieService:
    
    # Valid fields for sorting
    VALID_SORT_FIELDS = {
        'id', 'series_title', 'released_year', 'imdb_rating', 
        'meta_score', 'director', 'genre', 'created_at', 'no_of_votes'
    }
    
    @staticmethod
    def get_movies_paginated(
        db: Session,
        params: PaginationParams,
        search: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[str] = None,
        min_rating: Optional[float] = None
    ) -> Tuple[List[Movie], int]:
        """
        Get paginated movies with filtering, sorting, and full-text search
        
        Args:
            db: Database session
            params: Pagination parameters (page, page_size, sort_by, sort_order)
            search: Full-text search query
            genre: Filter by genre
            year: Filter by released year
            min_rating: Minimum IMDB rating
            
        Returns:
            Tuple of (movies list, total count)
        """
        query = db.query(Movie)
        
        # Full-text search using PostgreSQL
        if search:
            search_vector = func.to_tsvector(
                'english',
                func.coalesce(Movie.series_title, '') + ' ' +
                func.coalesce(Movie.overview, '') + ' ' +
                func.coalesce(Movie.director, '') + ' ' +
                func.coalesce(Movie.genre, '')
            )
            search_query = func.plainto_tsquery('english', search)
            
            query = query.filter(search_vector.op('@@')(search_query))
            
            # Order by relevance (ts_rank) when searching
            rank = func.ts_rank(search_vector, search_query)
            query = query.order_by(desc(rank))
        
        # Apply filters
        if genre:
            query = query.filter(Movie.genre.ilike(f'%{genre}%'))
        
        if year:
            query = query.filter(Movie.released_year == year)
        
        if min_rating is not None:
            query = query.filter(Movie.imdb_rating >= min_rating)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply sorting (only if not searching, as search has its own ranking)
        if not search and params.sort_by and params.sort_by in MovieService.VALID_SORT_FIELDS:
            sort_column = getattr(Movie, params.sort_by)
            
            if params.sort_order == 'asc':
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
        elif not search:
            # Default sorting by created_at desc
            query = query.order_by(desc(Movie.created_at))
        
        # Apply pagination
        offset = (params.page - 1) * params.page_size
        movies = query.offset(offset).limit(params.page_size).all()
        
        return movies, total
    
    @staticmethod
    def get_movie_by_id(db: Session, movie_id: int) -> Optional[Movie]:
        """Get movie by ID"""
        return db.query(Movie).filter(Movie.id == movie_id).first()
    
    @staticmethod
    def create_movie(db: Session, movie_data: MovieCreate) -> Movie:
        """Create new movie"""
        movie = Movie(**movie_data.model_dump())
        db.add(movie)
        db.commit()
        db.refresh(movie)
        return movie
    
    @staticmethod
    def update_movie(db: Session, movie_id: int, movie_data: MovieUpdate) -> Optional[Movie]:
        """Update existing movie"""
        movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if not movie:
            return None
        
        # Update only provided fields
        update_data = movie_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(movie, field, value)
        
        db.commit()
        db.refresh(movie)
        return movie
    
    @staticmethod
    def delete_movie(db: Session, movie_id: int) -> bool:
        """Delete movie by ID"""
        movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if not movie:
            return False
        
        db.delete(movie)
        db.commit()
        return True
    
    @staticmethod
    def search_movies(db: Session, query_text: str, limit: int = 10) -> List[Movie]:
        """
        Simple search movies by title, director, or overview
        (Legacy method, use get_movies_paginated with search parameter instead)
        """
        search_pattern = f"%{query_text}%"
        return db.query(Movie).filter(
            or_(
                Movie.series_title.ilike(search_pattern),
                Movie.director.ilike(search_pattern),
                Movie.overview.ilike(search_pattern)
            )
        ).limit(limit).all()
    
    # ==================== DASHBOARD STATISTICS ====================
    
    @staticmethod
    def get_stats_by_genre(db: Session) -> List[Dict]:
        """
        Get statistics by genre
        
        Returns:
            List of dicts with genre, count, and avg_rating
        """
        results = db.query(
            Movie.genre,
            func.count(Movie.id).label('count'),
            func.avg(Movie.imdb_rating).label('avg_rating')
        ).filter(
            Movie.genre.isnot(None)
        ).group_by(
            Movie.genre
        ).order_by(
            desc('count')
        ).all()
        
        return [
            {
                'genre': r.genre,
                'count': r.count,
                'avg_rating': round(r.avg_rating, 2) if r.avg_rating else None
            }
            for r in results
        ]
    
    @staticmethod
    def get_top_directors(db: Session, limit: int = 10) -> List[Dict]:
        """
        Get top directors by average rating
        
        Args:
            limit: Number of directors to return
            
        Returns:
            List of dicts with director, movie_count, avg_rating, total_votes
        """
        results = db.query(
            Movie.director,
            func.count(Movie.id).label('movie_count'),
            func.avg(Movie.imdb_rating).label('avg_rating'),
            func.sum(Movie.no_of_votes).label('total_votes')
        ).filter(
            Movie.director.isnot(None),
            Movie.imdb_rating.isnot(None)
        ).group_by(
            Movie.director
        ).having(
            func.count(Movie.id) >= 2  # At least 2 movies
        ).order_by(
            desc('avg_rating')
        ).limit(limit).all()
        
        return [
            {
                'director': r.director,
                'movie_count': r.movie_count,
                'avg_rating': round(r.avg_rating, 2) if r.avg_rating else None,
                'total_votes': r.total_votes
            }
            for r in results
        ]
    
    @staticmethod
    def get_movies_per_year(db: Session) -> List[Dict]:
        """
        Get number of movies per year
        
        Returns:
            List of dicts with year and count
        """
        results = db.query(
            Movie.released_year,
            func.count(Movie.id).label('count')
        ).filter(
            Movie.released_year.isnot(None)
        ).group_by(
            Movie.released_year
        ).order_by(
            Movie.released_year
        ).all()
        
        return [
            {
                'year': r.released_year,
                'count': r.count
            }
            for r in results
        ]
    
    @staticmethod
    def get_rating_distribution(db: Session) -> List[Dict]:
        """
        Get IMDB rating distribution (histogram)
        Ranges: 0-1, 1-2, 2-3, ..., 9-10
        
        Returns:
            List of dicts with rating_range and count
        """
        # Create rating ranges using CASE
        rating_range = case(
            (Movie.imdb_rating < 1, '0-1'),
            (Movie.imdb_rating < 2, '1-2'),
            (Movie.imdb_rating < 3, '2-3'),
            (Movie.imdb_rating < 4, '3-4'),
            (Movie.imdb_rating < 5, '4-5'),
            (Movie.imdb_rating < 6, '5-6'),
            (Movie.imdb_rating < 7, '6-7'),
            (Movie.imdb_rating < 8, '7-8'),
            (Movie.imdb_rating < 9, '8-9'),
            else_='9-10'
        )
        
        results = db.query(
            rating_range.label('rating_range'),
            func.count(Movie.id).label('count')
        ).filter(
            Movie.imdb_rating.isnot(None)
        ).group_by(
            rating_range
        ).order_by(
            rating_range
        ).all()
        
        return [
            {
                'rating_range': r.rating_range,
                'count': r.count
            }
            for r in results
        ]
    
    @staticmethod
    def get_meta_score_distribution(db: Session) -> List[Dict]:
        """
        Get Meta Score distribution (histogram)
        Ranges: 0-10, 10-20, ..., 90-100
        
        Returns:
            List of dicts with score_range and count
        """
        # Create meta score ranges
        score_range = case(
            (Movie.meta_score < 10, '0-10'),
            (Movie.meta_score < 20, '10-20'),
            (Movie.meta_score < 30, '20-30'),
            (Movie.meta_score < 40, '30-40'),
            (Movie.meta_score < 50, '40-50'),
            (Movie.meta_score < 60, '50-60'),
            (Movie.meta_score < 70, '60-70'),
            (Movie.meta_score < 80, '70-80'),
            (Movie.meta_score < 90, '80-90'),
            else_='90-100'
        )
        
        results = db.query(
            score_range.label('score_range'),
            func.count(Movie.id).label('count')
        ).filter(
            Movie.meta_score.isnot(None)
        ).group_by(
            score_range
        ).order_by(
            score_range
        ).all()
        
        return [
            {
                'score_range': r.score_range,
                'count': r.count
            }
            for r in results
        ]
    
    @staticmethod
    def get_dashboard_stats(db: Session) -> Dict:
        """
        Get overall dashboard statistics
        
        Returns:
            Dict with total counts and averages
        """
        total_movies = db.query(func.count(Movie.id)).scalar()
        
        total_directors = db.query(
            func.count(func.distinct(Movie.director))
        ).filter(
            Movie.director.isnot(None)
        ).scalar()
        
        total_genres = db.query(
            func.count(func.distinct(Movie.genre))
        ).filter(
            Movie.genre.isnot(None)
        ).scalar()
        
        avg_rating = db.query(
            func.avg(Movie.imdb_rating)
        ).filter(
            Movie.imdb_rating.isnot(None)
        ).scalar()
        
        avg_meta_score = db.query(
            func.avg(Movie.meta_score)
        ).filter(
            Movie.meta_score.isnot(None)
        ).scalar()
        
        return {
            'total_movies': total_movies,
            'total_directors': total_directors,
            'total_genres': total_genres,
            'avg_rating': round(avg_rating, 2) if avg_rating else None,
            'avg_meta_score': round(avg_meta_score, 2) if avg_meta_score else None
        }