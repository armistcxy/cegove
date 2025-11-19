from app.schemas.recommendation import (
    MovieRecommendation,
    RecommendationResponse,
    RecommendationRequest,
    CollaborativeRequest,
    ContentBasedRequest,
    PopularMoviesParams,
    TopRatedParams,
    SimilarMoviesParams,
    # Deprecated
    CollaborativeRecommendationRequest,
    CollaborativeRecommendationResponse,
    HybridRecommendationRequest
)

__all__ = [
    'MovieRecommendation',
    'RecommendationResponse',
    'RecommendationRequest',
    'CollaborativeRequest',
    'ContentBasedRequest',
    'PopularMoviesParams',
    'TopRatedParams',
    'SimilarMoviesParams',
    'CollaborativeRecommendationRequest',
    'CollaborativeRecommendationResponse',
    'HybridRecommendationRequest'
]