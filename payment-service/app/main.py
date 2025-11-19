from fastapi import FastAPI
from app.api.v1.payment_route import router as payment_router
from app.database.session import init_db
from app.services.payment_providers.provider_factory import PaymentProviderFactory
from app.services.payment_providers.vnpay_provider import VNPayProvider

app = FastAPI()

@app.on_event("startup")
async def startup():
    PaymentProviderFactory.register("vnpay", VNPayProvider)
    await init_db()
    

app.include_router(payment_router)
