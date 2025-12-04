from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.v1.payment import router as payment_router_v1
from app.api.v1.webhooks.payment_vnpay import router as payment_vnpay_webhook_router_v1
from app.database.session import init_db
from app.services.payment_providers.provider_factory import PaymentProviderFactory
from app.services.payment_providers.vnpay_provider import VNPayProvider
import os

app = FastAPI(
    title="Payment Service API",
    description="Payment processing service with VNPay provider integration.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add deprecation middleware for v1

@app.on_event("startup")
async def startup():
    PaymentProviderFactory.register("vnpay", VNPayProvider)
    await init_db()

# Include v1 routers
app.include_router(payment_router_v1)
app.include_router(payment_vnpay_webhook_router_v1)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

