"""
Payment Schema v2 - With Breaking Changes
========================================

Breaking Changes from v1 to v2:
1. Renamed field: 'booking_id' -> 'order_id'
2. Renamed field: 'provider' -> 'payment_provider'
3. Renamed field: 'status' -> 'payment_status'
4. Renamed field: 'amount' -> 'total_amount'
5. Added new required field: 'currency' (defaults to 'VND')
6. Response wraps data in 'result' object
"""

from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional


class PaymentBase_v2(BaseModel):
    order_id: int
    payment_provider: str
    total_amount: Decimal
    currency: str = "VND"


class PaymentCreate_v2(PaymentBase_v2):
    client_ip: str


class PaymentOut_v2(BaseModel):
    id: int
    order_id: int
    payment_provider: str
    total_amount: Decimal
    payment_status: str
    currency: str

    model_config = {"from_attributes": True}


class PaymentInitResponse_v2(BaseModel):
    result: PaymentOut_v2
    redirect_url: str


class PaymentUpdate_v2(BaseModel):
    order_id: Optional[int] = None
    payment_provider: Optional[str] = None
    total_amount: Optional[Decimal] = None
    payment_status: Optional[str] = None
    currency: Optional[str] = None
