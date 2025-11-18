from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.payment_service import PaymentService
from app.schema.payment import PaymentCreate

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])

service = PaymentService()


@router.post("/", response_model=dict)
async def create_payment(data: PaymentCreate, db: AsyncSession = Depends(get_db)):
    payment = await service.create_payment(db, data)
    return {"id": payment.id, "url": payment.url}

@router.get("/vnpay/ipn")
async def vnpay_ipn(request: Request, db: AsyncSession = Depends(get_db)):
    params = dict(request.query_params)
    ok = await service.handle_ipn(db, params)

    if ok:
        return {"RspCode": "00", "Message": "Success"}
    else:
        return {"RspCode": "97", "Message": "Failure"}

@router.get("/{payment_id}")
async def get_payment(payment_id: int, db: AsyncSession = Depends(get_db)):
    payment = await service.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(404, "Payment not found")
    return payment


@router.get("/")
async def list_payments(page: int = 1, per_page: int = 20, db: AsyncSession = Depends(get_db)):
    return await service.list_payments(db, page, per_page)

