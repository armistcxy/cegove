import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Tuple
from app.models.user_behavior import UserBehavior
from app.models.movie import Movie

class CollaborativeFilteringService:
    def __init__(self, n_factors: int = 10, learning_rate: float = 0.01, 
                 n_iterations: int = 100, regularization: float = 0.01):
        """
        Initialize Matrix Factorization model
        
        Args:
            n_factors: số lượng latent factors
            learning_rate: learning rate cho SGD
            n_iterations: số vòng lặp training
            regularization: lambda cho regularization
        """
        self.n_factors = n_factors
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.regularization = regularization
        self.user_factors = None
        self.item_factors = None
        self.user_id_map = {}
        self.movie_id_map = {}
        
    def _build_rating_matrix(self, db: Session) -> Tuple[np.ndarray, dict, dict]:
        """
        Xây dựng ma trận rating từ user behaviors
        """
        # Lấy tất cả behaviors và aggregate theo user-movie
        behaviors = db.query(
            UserBehavior.user_id,
            UserBehavior.movie_id,
            func.sum(UserBehavior.score).label('total_score')
        ).group_by(
            UserBehavior.user_id,
            UserBehavior.movie_id
        ).all()
        
        if not behaviors:
            return np.array([]), {}, {}
        
        # Tạo mapping từ user_id và movie_id sang index
        unique_users = sorted(set(b.user_id for b in behaviors))
        unique_movies = sorted(set(b.movie_id for b in behaviors))
        
        user_id_map = {user_id: idx for idx, user_id in enumerate(unique_users)}
        movie_id_map = {movie_id: idx for idx, movie_id in enumerate(unique_movies)}
        
        # Tạo rating matrix
        n_users = len(unique_users)
        n_movies = len(unique_movies)
        rating_matrix = np.zeros((n_users, n_movies))
        
        for behavior in behaviors:
            user_idx = user_id_map[behavior.user_id]
            movie_idx = movie_id_map[behavior.movie_id]
            rating_matrix[user_idx, movie_idx] = behavior.total_score
        
        return rating_matrix, user_id_map, movie_id_map
    
    def train(self, db: Session):
        """
        Train Matrix Factorization model sử dụng SGD
        """
        # Build rating matrix
        rating_matrix, user_id_map, movie_id_map = self._build_rating_matrix(db)
        
        if rating_matrix.size == 0:
            raise ValueError("Không có dữ liệu để train model")
        
        self.user_id_map = user_id_map
        self.movie_id_map = movie_id_map
        
        n_users, n_movies = rating_matrix.shape
        
        # Initialize factors randomly
        self.user_factors = np.random.normal(0, 0.1, (n_users, self.n_factors))
        self.item_factors = np.random.normal(0, 0.1, (n_movies, self.n_factors))
        
        # Get non-zero indices (observed ratings)
        user_indices, movie_indices = np.nonzero(rating_matrix)
        
        # Training loop
        for iteration in range(self.n_iterations):
            # Shuffle data
            indices = np.random.permutation(len(user_indices))
            
            for idx in indices:
                u = user_indices[idx]
                i = movie_indices[idx]
                
                # Predict
                prediction = np.dot(self.user_factors[u], self.item_factors[i])
                error = rating_matrix[u, i] - prediction
                
                # Update factors
                user_factor_update = (
                    self.learning_rate * 
                    (error * self.item_factors[i] - self.regularization * self.user_factors[u])
                )
                item_factor_update = (
                    self.learning_rate * 
                    (error * self.user_factors[u] - self.regularization * self.item_factors[i])
                )
                
                self.user_factors[u] += user_factor_update
                self.item_factors[i] += item_factor_update
    
    def predict(self, user_id: int, movie_id: int) -> float:
        """
        Dự đoán score cho một user-movie pair
        """
        if user_id not in self.user_id_map or movie_id not in self.movie_id_map:
            return 0.0
        
        user_idx = self.user_id_map[user_id]
        movie_idx = self.movie_id_map[movie_id]
        
        return float(np.dot(self.user_factors[user_idx], self.item_factors[movie_idx]))
    
    def recommend(self, user_id: int, top_n: int = 10, 
                  exclude_watched: bool = True, db: Session = None) -> List[Tuple[int, float]]:
        """
        Gợi ý top N movies cho user
        
        Returns:
            List of (movie_id, predicted_score)
        """
        if user_id not in self.user_id_map:
            return []
        
        user_idx = self.user_id_map[user_id]
        
        # Tính predicted scores cho tất cả movies
        all_movie_ids = list(self.movie_id_map.keys())
        predictions = []
        
        # Lấy danh sách movies đã xem (nếu cần exclude)
        watched_movies = set()
        if exclude_watched and db:
            watched = db.query(UserBehavior.movie_id).filter(
                UserBehavior.user_id == user_id
            ).distinct().all()
            watched_movies = {m[0] for m in watched}
        
        for movie_id in all_movie_ids:
            if exclude_watched and movie_id in watched_movies:
                continue
            
            movie_idx = self.movie_id_map[movie_id]
            score = float(np.dot(self.user_factors[user_idx], self.item_factors[movie_idx]))
            predictions.append((movie_id, score))
        
        # Sort by predicted score và lấy top N
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:top_n]

# Singleton instance
_cf_service = None

def get_cf_service() -> CollaborativeFilteringService:
    """
    Get or create collaborative filtering service instance
    """
    global _cf_service
    if _cf_service is None:
        _cf_service = CollaborativeFilteringService(
            n_factors=10,
            learning_rate=0.01,
            n_iterations=50,
            regularization=0.01
        )
    return _cf_service