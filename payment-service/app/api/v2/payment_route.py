"""
Payment Routes v2 - With Breaking Changes

Breaking Changes from v1:
- Field renames: booking_id -> order_id, provider -> payment_provider, etc.
- Response structure: 'payment' -> 'result', 'url' -> 'redirect_url'
- Added currency field
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.payment_service import PaymentService
from app.schema.payment_v2 import PaymentCreate_v2, PaymentInitResponse_v2, PaymentOut_v2

router = APIRouter(prefix="/api/v2/payments", tags=["Payments v2"])

service = PaymentService()


@router.post("/", response_model=PaymentInitResponse_v2)
async def create_payment_v2(data: PaymentCreate_v2, db: AsyncSession = Depends(get_db)):
    """
    Create a new payment (v2 API).
    
    **Breaking Changes from v1:**
    - Use 'order_id' instead of 'booking_id'
    - Use 'payment_provider' instead of 'provider'
    - Use 'total_amount' instead of 'amount'
    - Use 'payment_status' instead of 'status'
    - Response wraps payment in 'result' instead of 'payment'
    - Response uses 'redirect_url' instead of 'url'
    - Includes 'currency' field (required)
    """
    # Convert v2 schema to v1 schema for internal service
    from app.schema.payment import PaymentCreate
    v1_data = PaymentCreate(
        booking_id=data.order_id,
        provider=data.payment_provider,
        amount=data.total_amount,
        status="pending",
        client_ip=data.client_ip,
    )
    
    # Call v1 service
    v1_response = await service.create_payment(db, v1_data)
    
    # Convert v1 response to v2 schema
    v2_payment = PaymentOut_v2(
        id=v1_response.payment.id,
        order_id=v1_response.payment.booking_id,
        payment_provider=v1_response.payment.provider,
        total_amount=v1_response.payment.amount,
        payment_status=v1_response.payment.status,
        currency=data.currency,
    )
    
    return PaymentInitResponse_v2(result=v2_payment, redirect_url=v1_response.url)


@router.get("/vnpay/ipn")
async def vnpay_ipn_v2(request: Request, db: AsyncSession = Depends(get_db)):
    """
    VNPay IPN callback (v2).
    Same behavior as v1, no breaking changes for webhook endpoints.
    """
    params = dict(request.query_params)
    ok = await service.handle_ipn(db, params)

    if ok:
        return {"RspCode": "00", "Message": "Success"}
    else:
        return {"RspCode": "97", "Message": "Failure"}


@router.get("/vnpay/return")
async def vnpay_return_v2(request: Request):
    """
    VNPay return URL (v2).
    Same behavior as v1, no breaking changes for user redirect.
    """
    params = dict(request.query_params)
    if params.get("vnp_ResponseCode") == "00":
        return {"message": "Payment success. Waiting for confirmation."}
    else:
        return {"message": "Payment failed."}


@router.get("/{payment_id}")
async def get_payment_v2(payment_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get payment details (v2).
    
    **Breaking Changes from v1:**
    - Response field names renamed: booking_id -> order_id, etc.
    - Includes 'currency' field
    """
    payment = await service.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(404, "Payment not found")
    
    # Convert to v2 schema
    return PaymentOut_v2(
        id=payment.id,
        order_id=payment.booking_id,
        payment_provider=payment.provider,
        total_amount=payment.amount,
        payment_status=payment.status,
        currency="VND",  # Default currency
    )


@router.get("/")
async def list_payments_v2(page: int = 1, per_page: int = 20, db: AsyncSession = Depends(get_db)):
    """
    List all payments (v2).
    
    **Breaking Changes from v1:**
    - Response field names renamed: booking_id -> order_id, etc.
    - Each payment includes 'currency' field
    """
    payments = await service.list_payments(db, page, per_page)
    
    # Convert list to v2 schema
    return [
        PaymentOut_v2(
            id=p.id,
            order_id=p.booking_id,
            payment_provider=p.provider,
            total_amount=p.amount,
            payment_status=p.status,
            currency="VND",  # Default currency
        )
        for p in payments
    ]
