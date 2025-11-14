from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from typing import List, Optional, Tuple
from app.models.movie import Movie
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class RecommendationService:
    """
    Recommendation Service for movie suggestions
    
    Methods:
    1. Popular movies - based on votes and ratings
    2. Top rated movies - highest IMDB ratings
    3. Content-based - TF-IDF similarity on genre, director, overview
    """
    
    @staticmethod
    def get_popular_movies(
        db: Session,
        limit: int = 10,
        min_votes: int = 10000
    ) -> List[Tuple[Movie, str]]:
        """
        Get popular movies based on number of votes and rating
        
        Popularity score = (no_of_votes / 1000) * imdb_rating
        
        Args:
            db: Database session
            limit: Number of movies to return
            min_votes: Minimum number of votes required
            
        Returns:
            List of tuples (Movie, reason)
        """
        movies = db.query(Movie).filter(
            and_(
                Movie.no_of_votes.isnot(None),
                Movie.no_of_votes >= min_votes,
                Movie.imdb_rating.isnot(None)
            )
        ).order_by(
            desc(Movie.no_of_votes),
            desc(Movie.imdb_rating)
        ).limit(limit).all()
        
        # Add reason
        results = [
            (movie, f"Popular with {movie.no_of_votes:,} votes")
            for movie in movies
        ]
        
        return results
    
    @staticmethod
    def get_top_rated_movies(
        db: Session,
        limit: int = 10,
        min_votes: int = 5000
    ) -> List[Tuple[Movie, str]]:
        """
        Get top rated movies by IMDB rating
        
        Args:
            db: Database session
            limit: Number of movies to return
            min_votes: Minimum number of votes to be considered
            
        Returns:
            List of tuples (Movie, reason)
        """
        movies = db.query(Movie).filter(
            and_(
                Movie.imdb_rating.isnot(None),
                Movie.no_of_votes.isnot(None),
                Movie.no_of_votes >= min_votes
            )
        ).order_by(
            desc(Movie.imdb_rating),
            desc(Movie.no_of_votes)
        ).limit(limit).all()
        
        # Add reason
        results = [
            (movie, f"High rating: {movie.imdb_rating}/10")
            for movie in movies
        ]
        
        return results
    
    @staticmethod
    def get_similar_movies_content_based(
        db: Session,
        movie_id: int,
        limit: int = 10
    ) -> Tuple[Optional[Movie], List[Tuple[Movie, float, str]]]:
        """
        Get similar movies using content-based filtering (TF-IDF)
        
        Uses TF-IDF on combined features:
        - Genre
        - Director
        - Overview
        - Stars
        
        Args:
            db: Database session
            movie_id: Source movie ID
            limit: Number of recommendations
            
        Returns:
            Tuple of (source_movie, List of (Movie, similarity_score, reason))
        """
        # Get source movie
        source_movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if not source_movie:
            return None, []
        
        # Get all movies with necessary data
        all_movies = db.query(Movie).filter(
            and_(
                Movie.id != movie_id,  # Exclude source movie
                Movie.overview.isnot(None)
            )
        ).all()
        
        if not all_movies:
            return source_movie, []
        
        # Create feature text for each movie
        def create_feature_text(movie: Movie) -> str:
            """Combine movie features into single text"""
            features = []
            
            if movie.genre:
                # Repeat genre 2 times to give it more weight
                features.append(movie.genre * 2)
            
            if movie.director:
                # Repeat director 2 times
                features.append(movie.director * 2)
            
            if movie.overview:
                features.append(movie.overview)
            
            # Add stars
            for star in [movie.star1, movie.star2, movie.star3, movie.star4]:
                if star:
                    features.append(star)
            
            return " ".join(features)
        
        # Create feature texts
        source_text = create_feature_text(source_movie)
        movie_texts = [create_feature_text(m) for m in all_movies]
        
        # Add source movie at the beginning
        all_texts = [source_text] + movie_texts
        
        # TF-IDF Vectorization
        tfidf = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2)  # Unigrams and bigrams
        )
        
        try:
            tfidf_matrix = tfidf.fit_transform(all_texts)
            
            # Calculate cosine similarity
            # First row is source movie, compare with all others
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            
            # Get top similar movies
            similar_indices = similarities.argsort()[::-1][:limit]
            
            results = []
            for idx in similar_indices:
                movie = all_movies[idx]
                similarity = float(similarities[idx])
                
                # Create reason based on similarity
                if similarity > 0.5:
                    reason = f"Very similar ({similarity:.0%} match)"
                elif similarity > 0.3:
                    reason = f"Similar genre and style ({similarity:.0%} match)"
                else:
                    reason = f"Related content ({similarity:.0%} match)"
                
                results.append((movie, similarity, reason))
            
            return source_movie, results
            
        except Exception as e:
            print(f"Error in TF-IDF: {str(e)}")
            return source_movie, []
    
    @staticmethod
    def get_movies_by_genre(
        db: Session,
        genre: str,
        limit: int = 10,
        exclude_movie_id: Optional[int] = None
    ) -> List[Tuple[Movie, str]]:
        """
        Get movies by genre (fallback for content-based)
        
        Args:
            db: Database session
            genre: Genre to filter
            limit: Number of movies
            exclude_movie_id: Movie ID to exclude
            
        Returns:
            List of tuples (Movie, reason)
        """
        query = db.query(Movie).filter(
            and_(
                Movie.genre.ilike(f'%{genre}%'),
                Movie.imdb_rating.isnot(None)
            )
        )
        
        if exclude_movie_id:
            query = query.filter(Movie.id != exclude_movie_id)
        
        movies = query.order_by(
            desc(Movie.imdb_rating)
        ).limit(limit).all()
        
        results = [
            (movie, f"Same genre: {genre}")
            for movie in movies
        ]
        
        return results