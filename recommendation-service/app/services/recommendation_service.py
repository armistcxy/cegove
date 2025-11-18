from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.models.movie import Movie


class RecommendationService:
    """Service for content-based and popularity-based recommendations"""
    
    # Class-level cache for TF-IDF (shared across instances in same process)
    _tfidf_cache = {
        'vectorizer': None,
        'matrix': None,
        'movie_ids': None,
        'movies': None
    }
    
    def __init__(self, db: Session = None):
        """
        Initialize recommendation service
        
        Args:
            db: SQLAlchemy database session (optional for some methods)
        """
        self.db = db
    
    @classmethod
    def clear_content_cache(cls):
        """Clear TF-IDF cache (call after data updates)"""
        cls._tfidf_cache = {
            'vectorizer': None,
            'matrix': None,
            'movie_ids': None,
            'movies': None
        }
    
    def _build_feature_string(self, movie: Movie) -> str:
        """
        Build feature string for TF-IDF from movie attributes
        Includes: genre, director, overview, cast (star1-star4)
        """
        features = []
        
        if movie.genre:
            features.append(movie.genre.replace(',', ' '))
        
        if movie.director:
            features.append(movie.director)
        
        if movie.overview:
            features.append(movie.overview)
        
        # Add cast members (star1, star2, star3, star4)
        for star_attr in ['star1', 'star2', 'star3', 'star4']:
            star = getattr(movie, star_attr, None)
            if star:
                features.append(star)
        
        return ' '.join(features)
    
    def _ensure_tfidf_cache(self, all_movies: List[Movie]):
        """
        Build or reuse TF-IDF vectorizer and matrix
        Cache is invalidated when movie IDs change
        """
        current_movie_ids = [m.id for m in all_movies]
        
        # Check if cache is valid
        if (self._tfidf_cache['movie_ids'] is not None and 
            self._tfidf_cache['movie_ids'] == current_movie_ids):
            return  # Cache is valid, no rebuild needed
        
        # Rebuild TF-IDF
        feature_strings = [self._build_feature_string(m) for m in all_movies]
        
        vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2)
        )
        
        tfidf_matrix = vectorizer.fit_transform(feature_strings)
        
        # Update cache
        self._tfidf_cache['vectorizer'] = vectorizer
        self._tfidf_cache['matrix'] = tfidf_matrix
        self._tfidf_cache['movie_ids'] = current_movie_ids
        self._tfidf_cache['movies'] = all_movies
    
    def get_popular_movies(
        self, 
        limit: int = 10, 
        min_votes: int = 10000
    ) -> List[Tuple[Movie, str]]:
        """
        Get popular movies based on IMDB rating and vote count
        
        Args:
            limit: Number of movies to return
            min_votes: Minimum number of votes required
            
        Returns:
            List of tuples (Movie, reason)
        """
        if not self.db:
            raise ValueError("Database session required for this method")
        
        movies = (
            self.db.query(Movie)
            .filter(Movie.no_of_votes >= min_votes)
            .order_by(desc(Movie.imdb_rating), desc(Movie.no_of_votes))
            .limit(limit)
            .all()
        )
        
        return [
            (movie, f"Phim phổ biến - Rating {movie.imdb_rating}/10 với {movie.no_of_votes:,} votes")
            for movie in movies
        ]
    
    def get_top_rated_movies(
        self, 
        limit: int = 10, 
        min_votes: int = 5000
    ) -> List[Tuple[Movie, str]]:
        """
        Get top rated movies based on IMDB rating
        
        Args:
            limit: Number of movies to return
            min_votes: Minimum number of votes required
            
        Returns:
            List of tuples (Movie, reason)
        """
        if not self.db:
            raise ValueError("Database session required for this method")
        
        movies = (
            self.db.query(Movie)
            .filter(Movie.no_of_votes >= min_votes)
            .order_by(desc(Movie.imdb_rating))
            .limit(limit)
            .all()
        )
        
        return [
            (movie, f"Top rated - {movie.imdb_rating}/10")
            for movie in movies
        ]
    
    def get_similar_movies_content_based(
        self,
        db: Session,
        movie_id: int,
        limit: int = 10
    ) -> Tuple[Optional[Movie], List[Tuple[Movie, float, str]]]:
        """
        Get similar movies using TF-IDF content-based filtering with caching
        
        Features used: genre, director, overview, cast (star1-star4)
        
        Args:
            db: Database session
            movie_id: Source movie ID
            limit: Number of similar movies to return
            
        Returns:
            Tuple of (source_movie, [(similar_movie, similarity_score, reason)])
        """
        source_movie = db.query(Movie).filter(Movie.id == movie_id).first()
        
        if not source_movie:
            return None, []
        
        # Get all movies
        all_movies = db.query(Movie).all()
        
        if len(all_movies) < 2:
            return source_movie, []
        
        # Ensure TF-IDF cache is built/updated
        self._ensure_tfidf_cache(all_movies)
        
        # Get cached data
        tfidf_matrix = self._tfidf_cache['matrix']
        cached_movie_ids = self._tfidf_cache['movie_ids']
        cached_movies = self._tfidf_cache['movies']
        
        # Find source movie index
        try:
            source_idx = cached_movie_ids.index(movie_id)
        except ValueError:
            return source_movie, []
        
        # Compute cosine similarity (fast because matrix is cached)
        cosine_sim = cosine_similarity(
            tfidf_matrix[source_idx:source_idx+1], 
            tfidf_matrix
        ).flatten()
        
        # Get top similar movies (exclude source)
        similar_indices = np.argsort(cosine_sim)[::-1]
        similar_indices = [idx for idx in similar_indices if idx != source_idx]
        
        results = []
        for idx in similar_indices:
            if len(results) >= limit:
                break
                
            similarity = float(cosine_sim[idx])
            
            # Skip very low similarity
            if similarity <= 0.01:
                continue
            
            similar_movie = cached_movies[idx]
            
            # Build reason with common features
            common_features = []
            
            if source_movie.genre and similar_movie.genre:
                source_genres = set(g.strip() for g in source_movie.genre.split(','))
                similar_genres = set(g.strip() for g in similar_movie.genre.split(','))
                common = source_genres & similar_genres
                if common:
                    common_features.append(f"cùng thể loại {', '.join(list(common)[:2])}")
            
            if source_movie.director and similar_movie.director:
                if source_movie.director == similar_movie.director:
                    common_features.append(f"cùng đạo diễn {source_movie.director}")
            
            # Check common cast members
            source_cast = set()
            for attr in ['star1', 'star2', 'star3', 'star4']:
                star = getattr(source_movie, attr, None)
                if star:
                    source_cast.add(star)
            
            similar_cast = set()
            for attr in ['star1', 'star2', 'star3', 'star4']:
                star = getattr(similar_movie, attr, None)
                if star:
                    similar_cast.add(star)
            
            common_cast = source_cast & similar_cast
            if common_cast:
                common_features.append(f"cùng diễn viên {', '.join(list(common_cast)[:2])}")
            
            reason = f"Tương tự {round(similarity * 100, 1)}%"
            if common_features:
                reason += f" ({', '.join(common_features[:2])})"
            
            results.append((similar_movie, similarity, reason))
        
        return source_movie, results
    
    def get_movies_by_genre(
        self,
        db: Session,
        genre: str,
        limit: int = 10,
        exclude_movie_id: Optional[int] = None
    ) -> List[Tuple[Movie, str]]:
        """
        Get movies by genre, sorted by rating
        
        Args:
            db: Database session
            genre: Genre to filter by
            limit: Number of movies to return
            exclude_movie_id: Movie ID to exclude from results
            
        Returns:
            List of tuples (Movie, reason)
        """
        query = db.query(Movie).filter(Movie.genre.ilike(f'%{genre}%'))
        
        if exclude_movie_id:
            query = query.filter(Movie.id != exclude_movie_id)
        
        movies = (
            query
            .order_by(desc(Movie.imdb_rating))
            .limit(limit)
            .all()
        )
        
        return [
            (movie, f"Thể loại {genre} - Rating {movie.imdb_rating}/10")
            for movie in movies
        ]