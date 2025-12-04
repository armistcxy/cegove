from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/api/v1/payments/vnpay", tags=["VNPAY"])
service = PaymentService()

@router.get("/ipn")
async def vnpay_ipn(request: Request, db: AsyncSession = Depends(get_db)):
    params = dict(request.query_params)
    ok = await service.handle_ipn(db, params)

    if ok:
        return {"RspCode": "00", "Message": "Success"}
    else:
        return {"RspCode": "97", "Message": "Failure"}

@router.get("/return")
async def vnpay_return(request: Request):
    params = dict(request.query_params)
    if params.get("vnp_ResponseCode") == "00":
        return {"message": "Payment success. Waiting for confirmation."}
    else:
        return {"message": "Payment failed."}
