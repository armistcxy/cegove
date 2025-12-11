import numpy as np
import pickle
import os
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Tuple, Optional, Dict
from datetime import datetime
import logging

from app.models.user_behavior import UserBehavior
from app.models.movie import Movie

logger = logging.getLogger(__name__)

class CollaborativeFilteringService:
    def __init__(
        self, 
        n_factors: int = 20, 
        learning_rate: float = 0.01,
        n_iterations: int = 100, 
        regularization: float = 0.02,
        model_path: str = "weights/cf_model.pkl",
        min_interactions: int = 3,
        lr_decay: float = 0.95,
        random_seed: int = 42
    ):
        """
        Initialize Matrix Factorization model với bias terms
        
        Args:
            n_factors: số lượng latent factors
            learning_rate: learning rate cho SGD
            n_iterations: số vòng lặp training
            regularization: lambda cho regularization
            model_path: đường dẫn lưu model
            min_interactions: số tương tác tối thiểu để user được coi là "active"
            lr_decay: tỷ lệ giảm learning rate mỗi epoch
            random_seed: seed cho reproducibility
        """
        self.n_factors = n_factors
        self.initial_lr = learning_rate
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.regularization = regularization
        self.model_path = model_path
        self.min_interactions = min_interactions
        self.lr_decay = lr_decay
        
        # Set random seed
        np.random.seed(random_seed)
        
        # Model parameters
        self.user_factors = None
        self.item_factors = None
        self.user_bias = None
        self.item_bias = None
        self.global_mean = 0.0
        
        # Mappings
        self.user_id_map = {}
        self.movie_id_map = {}
        self.reverse_user_map = {}
        self.reverse_movie_map = {}
        
        # Cache
        self._recommendation_cache = {}
        self._last_train_time = None
        
        # Load model if exists
        self._load_model()
    
    def _build_sparse_rating_data(self, db: Session) -> Tuple[List, Dict, Dict]:
        """
        Xây dựng sparse rating data từ user behaviors
        Trả về list of (user_idx, item_idx, rating) thay vì dense matrix
        """
        # Aggregate behaviors theo user-movie
        behaviors = db.query(
            UserBehavior.user_id,
            UserBehavior.movie_id,
            func.sum(UserBehavior.score).label('total_score'),
            func.count(UserBehavior.id).label('interaction_count')
        ).group_by(
            UserBehavior.user_id,
            UserBehavior.movie_id
        ).all()
        
        if not behaviors:
            return [], {}, {}
        
        # Tạo mapping
        unique_users = sorted(set(b.user_id for b in behaviors))
        unique_movies = sorted(set(b.movie_id for b in behaviors))
        
        user_id_map = {user_id: idx for idx, user_id in enumerate(unique_users)}
        movie_id_map = {movie_id: idx for idx, movie_id in enumerate(unique_movies)}
        
        # Tạo sparse rating list
        rating_data = []
        for behavior in behaviors:
            user_idx = user_id_map[behavior.user_id]
            movie_idx = movie_id_map[behavior.movie_id]
            rating = behavior.total_score
            rating_data.append((user_idx, movie_idx, rating))
        
        return rating_data, user_id_map, movie_id_map
    
    def _initialize_factors(self, n_users: int, n_movies: int):
        """
        Khởi tạo factors và bias với phân phối normal nhỏ
        """
        scale = 0.1 / np.sqrt(self.n_factors)
        self.user_factors = np.random.normal(0, scale, (n_users, self.n_factors))
        self.item_factors = np.random.normal(0, scale, (n_movies, self.n_factors))
        self.user_bias = np.zeros(n_users)
        self.item_bias = np.zeros(n_movies)
    
    def _compute_global_mean(self, rating_data: List[Tuple]) -> float:
        """
        Tính global mean rating
        """
        if not rating_data:
            return 0.0
        return np.mean([r[2] for r in rating_data])
    
    def train(self, db: Session, verbose: bool = True):
        """
        Train Matrix Factorization model với SGD và bias terms
        """
        logger.info("Starting collaborative filtering training...")
        
        # Build sparse rating data
        rating_data, user_id_map, movie_id_map = self._build_sparse_rating_data(db)
        
        if not rating_data:
            raise ValueError("Không có dữ liệu để train model")
        
        self.user_id_map = user_id_map
        self.movie_id_map = movie_id_map
        
        # Create reverse mappings
        self.reverse_user_map = {v: k for k, v in user_id_map.items()}
        self.reverse_movie_map = {v: k for k, v in movie_id_map.items()}
        
        n_users = len(user_id_map)
        n_movies = len(movie_id_map)
        
        # Initialize factors and bias
        self._initialize_factors(n_users, n_movies)
        
        # Compute global mean
        self.global_mean = self._compute_global_mean(rating_data)
        
        logger.info(f"Training with {n_users} users, {n_movies} movies, {len(rating_data)} ratings")
        logger.info(f"Global mean rating: {self.global_mean:.2f}")
        
        # Convert to numpy array for faster indexing
        rating_array = np.array(rating_data)
        n_ratings = len(rating_array)
        
        # Training loop với learning rate decay
        for iteration in range(self.n_iterations):
            # Shuffle data
            np.random.shuffle(rating_array)
            
            total_error = 0.0
            
            # SGD updates
            for user_idx, item_idx, rating in rating_array:
                user_idx, item_idx = int(user_idx), int(item_idx)
                
                # Predict
                prediction = (
                    self.global_mean + 
                    self.user_bias[user_idx] + 
                    self.item_bias[item_idx] +
                    np.dot(self.user_factors[user_idx], self.item_factors[item_idx])
                )
                
                error = rating - prediction
                total_error += error ** 2
                
                # Update biases
                self.user_bias[user_idx] += self.learning_rate * (
                    error - self.regularization * self.user_bias[user_idx]
                )
                self.item_bias[item_idx] += self.learning_rate * (
                    error - self.regularization * self.item_bias[item_idx]
                )
                
                # Update factors
                user_factor_old = self.user_factors[user_idx].copy()
                
                self.user_factors[user_idx] += self.learning_rate * (
                    error * self.item_factors[item_idx] - 
                    self.regularization * self.user_factors[user_idx]
                )
                
                self.item_factors[item_idx] += self.learning_rate * (
                    error * user_factor_old - 
                    self.regularization * self.item_factors[item_idx]
                )
            
            # Compute RMSE
            rmse = np.sqrt(total_error / n_ratings)
            
            # Learning rate decay
            self.learning_rate *= self.lr_decay
            
            if verbose and (iteration + 1) % 10 == 0:
                logger.info(f"Iteration {iteration + 1}/{self.n_iterations} - RMSE: {rmse:.4f}, LR: {self.learning_rate:.6f}")
        
        # Clear cache after training
        self._recommendation_cache.clear()
        self._last_train_time = datetime.now()
        
        # Save model
        self._save_model()
        
        logger.info("Training completed successfully!")
        
        return {
            "n_users": n_users,
            "n_movies": n_movies,
            "n_ratings": n_ratings,
            "final_rmse": rmse,
            "global_mean": self.global_mean
        }
    
    def predict(self, user_id: int, movie_id: int) -> float:
        """
        Dự đoán score cho một user-movie pair
        """
        if self.user_factors is None:
            return self.global_mean
        
        # Check if user exists
        if user_id not in self.user_id_map:
            # Cold-start user: return item bias + global mean
            if movie_id in self.movie_id_map:
                movie_idx = self.movie_id_map[movie_id]
                return self.global_mean + self.item_bias[movie_idx]
            return self.global_mean
        
        # Check if movie exists
        if movie_id not in self.movie_id_map:
            # Cold-start item: return user bias + global mean
            user_idx = self.user_id_map[user_id]
            return self.global_mean + self.user_bias[user_idx]
        
        user_idx = self.user_id_map[user_id]
        movie_idx = self.movie_id_map[movie_id]
        
        prediction = (
            self.global_mean +
            self.user_bias[user_idx] +
            self.item_bias[movie_idx] +
            np.dot(self.user_factors[user_idx], self.item_factors[movie_idx])
        )
        
        return float(prediction)
    
    def _get_watched_movies(self, user_id: int, db: Session) -> set:
        """
        Lấy danh sách movies đã xem của user
        """
        watched = db.query(UserBehavior.movie_id).filter(
            UserBehavior.user_id == user_id
        ).distinct().all()
        return {m[0] for m in watched}
    
    def recommend(
        self, 
        user_id: int, 
        top_n: int = 10,
        exclude_watched: bool = True, 
        db: Session = None
    ) -> List[Tuple[int, float]]:
        """
        Gợi ý top N movies cho user (vectorized)
        """
        if self.user_factors is None:
            return []
        
        # Check cache
        cache_key = f"{user_id}_{top_n}_{exclude_watched}"
        if cache_key in self._recommendation_cache:
            return self._recommendation_cache[cache_key]
        
        # Get watched movies
        watched_movies = set()
        if exclude_watched and db:
            watched_movies = self._get_watched_movies(user_id, db)
        
        # User không có trong training set (cold-start)
        if user_id not in self.user_id_map:
            # Return popular items based on item bias
            all_movie_ids = list(self.movie_id_map.keys())
            predictions = []
            
            for movie_id in all_movie_ids:
                if movie_id in watched_movies:
                    continue
                movie_idx = self.movie_id_map[movie_id]
                score = self.global_mean + self.item_bias[movie_idx]
                predictions.append((movie_id, score))
            
            predictions.sort(key=lambda x: x[1], reverse=True)
            result = predictions[:top_n]
            self._recommendation_cache[cache_key] = result
            return result
        
        user_idx = self.user_id_map[user_id]
        
        # Vectorized prediction cho tất cả movies
        all_movie_ids = np.array(list(self.movie_id_map.keys()))
        all_movie_indices = np.array([self.movie_id_map[mid] for mid in all_movie_ids])
        
        # Compute scores vectorized
        scores = (
            self.global_mean +
            self.user_bias[user_idx] +
            self.item_bias[all_movie_indices] +
            np.dot(self.item_factors[all_movie_indices], self.user_factors[user_idx])
        )
        
        # Filter watched movies
        if exclude_watched:
            mask = np.array([mid not in watched_movies for mid in all_movie_ids])
            all_movie_ids = all_movie_ids[mask]
            scores = scores[mask]
        
        # Get top N
        if len(scores) == 0:
            return []
        
        top_indices = np.argsort(scores)[::-1][:top_n]
        predictions = [(int(all_movie_ids[i]), float(scores[i])) for i in top_indices]
        
        # Cache result
        self._recommendation_cache[cache_key] = predictions
        
        return predictions
    
    def is_cold_start_user(self, user_id: int, db: Session) -> bool:
        """
        Kiểm tra user có phải cold-start không
        """
        if user_id not in self.user_id_map:
            return True
        
        # Check số lượng interactions
        interaction_count = db.query(func.count(UserBehavior.id)).filter(
            UserBehavior.user_id == user_id
        ).scalar()
        
        return interaction_count < self.min_interactions
    
    def _save_model(self):
        """
        Lưu model ra disk
        """
        try:
            model_dir = Path(self.model_path).parent
            model_dir.mkdir(parents=True, exist_ok=True)
            
            model_data = {
                'user_factors': self.user_factors,
                'item_factors': self.item_factors,
                'user_bias': self.user_bias,
                'item_bias': self.item_bias,
                'global_mean': self.global_mean,
                'user_id_map': self.user_id_map,
                'movie_id_map': self.movie_id_map,
                'reverse_user_map': self.reverse_user_map,
                'reverse_movie_map': self.reverse_movie_map,
                'n_factors': self.n_factors,
                'last_train_time': self._last_train_time,
                'min_interactions': self.min_interactions
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Model saved to {self.model_path}")
            
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def _load_model(self):
        """
        Load model từ disk
        """
        try:
            if not os.path.exists(self.model_path):
                logger.info("No saved model found. Will train new model.")
                return
            
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.user_factors = model_data['user_factors']
            self.item_factors = model_data['item_factors']
            self.user_bias = model_data['user_bias']
            self.item_bias = model_data['item_bias']
            self.global_mean = model_data['global_mean']
            self.user_id_map = model_data['user_id_map']
            self.movie_id_map = model_data['movie_id_map']
            self.reverse_user_map = model_data['reverse_user_map']
            self.reverse_movie_map = model_data['reverse_movie_map']
            self._last_train_time = model_data.get('last_train_time')
            
            logger.info(f"Model loaded from {self.model_path}")
            logger.info(f"Last trained: {self._last_train_time}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
    
    def get_model_info(self) -> Dict:
        """
        Lấy thông tin về model
        """
        if self.user_factors is None:
            return {"status": "not_trained"}
        
        return {
            "status": "trained",
            "n_users": len(self.user_id_map),
            "n_movies": len(self.movie_id_map),
            "n_factors": self.n_factors,
            "global_mean": self.global_mean,
            "last_train_time": self._last_train_time.isoformat() if self._last_train_time else None,
            "cache_size": len(self._recommendation_cache)
        }
    
    def clear_cache(self):
        """
        Xóa recommendation cache
        """
        self._recommendation_cache.clear()
        logger.info("Recommendation cache cleared")


# Singleton instance
_cf_service = None

def get_cf_service() -> CollaborativeFilteringService:
    """
    Get or create collaborative filtering service instance
    """
    global _cf_service
    if _cf_service is None:
        _cf_service = CollaborativeFilteringService(
            n_factors=20,
            learning_rate=0.01,
            n_iterations=100,
            regularization=0.02,
            model_path="weights/cf_model.pkl",
            min_interactions=3,
            lr_decay=0.95,
            random_seed=42
        )
    return _cf_service