from fastapi import APIRouter
from app.api.v1.endpoints import recommendations
from app.api.v1.endpoints import collaborative

api_router = APIRouter()

api_router.include_router(
    recommendations.router,
    prefix="/recommendations",
    tags=["recommendations"]
)

api_router.include_router(
    collaborative.router,
    prefix="/collaborative",
    tags=["collaborative-filtering"]
)