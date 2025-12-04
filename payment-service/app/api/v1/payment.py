from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.payment_service import PaymentService
from app.schema.payment import PaymentCreate, PaymentInitResponse

router = APIRouter(prefix="/api/v1/payments")
service = PaymentService()

@router.post("/", response_model=PaymentInitResponse, tags=["Payments"])
async def create_payment(data: PaymentCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_payment(db, data)

@router.get("/{payment_id}", tags=["Payments"])
async def get_payment(payment_id: int, db: AsyncSession = Depends(get_db)):
    payment = await service.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(404, "Payment not found")
    return payment

@router.get("/", tags=["Payments"])
async def list_payments(page: int = 1, per_page: int = 20, db: AsyncSession = Depends(get_db)):
    return await service.list_payments(db, page, per_page)
