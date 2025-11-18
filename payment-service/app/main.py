from fastapi import FastAPI
from app.api.v1.payment_route import router as payment_router

app = FastAPI()

app.include_router(payment_router)
