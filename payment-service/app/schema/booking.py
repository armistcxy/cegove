from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class BookingBase(BaseModel):
    user_id: int
    screening_id: int
    total_amount: Decimal
    status: str


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BaseModel):
    user_id: Optional[int] = None
    screening_id: Optional[int] = None
    total_amount: Optional[Decimal] = None
    status: Optional[str] = None


class BookingResponse(BookingBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True