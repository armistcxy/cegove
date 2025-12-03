from fastapi import APIRouter
from app.api.v1.endpoints import comments, sentiment

api_router = APIRouter()

api_router.include_router(
    comments.router,
    prefix="/comments",
    tags=["comments"]
)
api_router.include_router(
    sentiment.router,
    prefix="/sentiment",
    tags=["sentiment"]
)