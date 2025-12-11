from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/api/v1/webhooks/vnpay", tags=["VNPAY Webhook"])
service = PaymentService()

@router.get("/ipn")
async def vnpay_ipn(request: Request, db: AsyncSession = Depends(get_db)):
    params = dict(request.query_params)
    print(f"IPN received with params: {params}")
    resp_code, message = await service.handle_ipn(db, params)
    print(f"IPN response: {resp_code} - {message}")

    return {"RspCode": resp_code, "Message": message}

@router.get("/return")
async def vnpay_return(request: Request, db: AsyncSession = Depends(get_db)):
    params = dict(request.query_params)
    print(f"Return URL called with params: {params}")
    
    # If payment failed/cancelled, update the status
    if params.get("vnp_ResponseCode") != "00":
        txn_ref = params.get("vnp_TxnRef")
        if txn_ref:
            resp_code, message = await service.handle_ipn(db, params)
            print(f"Return URL - Payment updated: {resp_code} - {message}")
    
    # Redirect to frontend payment result page with all query parameters
    query_string = str(request.query_params)
    frontend_url = f"https://cegove.cloud/payment-result?{query_string}"
    return RedirectResponse(url=frontend_url)