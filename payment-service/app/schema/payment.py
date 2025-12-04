from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional

class PaymentBase(BaseModel):
    booking_id: int
    provider: str
    amount: Decimal
    # status: str


class PaymentCreate(PaymentBase):
    client_ip: str

class PaymentOut(BaseModel):
    id: int
    booking_id: int
    provider: str
    amount: Decimal
    status: str

    model_config = {"from_attributes": True}


class PaymentInitResponse(BaseModel):
    payment: PaymentOut  # nested object
    url: str



class PaymentUpdate(BaseModel):
    booking_id: Optional[int] = None
    provider: Optional[str] = None
    amount: Optional[Decimal] = None
    status: Optional[str] = None


class PaymentResponse(PaymentBase):
    id: int
    transaction_time: datetime

    class Config:
        from_attributes = True
