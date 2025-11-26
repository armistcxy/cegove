from fastapi import FastAPI
from app.api.v1.payment_route import router as payment_router_v1
from app.api.v2.payment_route import router as payment_router_v2
from app.middleware.deprecation import DeprecationMiddleware
from app.database.session import init_db
from app.services.payment_providers.provider_factory import PaymentProviderFactory
from app.services.payment_providers.vnpay_provider import VNPayProvider

app = FastAPI(
    title="Payment Service API",
    description="Payment processing service with VNPay provider integration. v2 is the current version.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add deprecation middleware for v1
app.add_middleware(DeprecationMiddleware)

@app.on_event("startup")
async def startup():
    PaymentProviderFactory.register("vnpay", VNPayProvider)
    await init_db()

# Include both v1 and v2 routers
app.include_router(payment_router_v1)
app.include_router(payment_router_v2)

