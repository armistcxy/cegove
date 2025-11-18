from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class BookingSeatBase(BaseModel):
    booking_id: int
    seat_id: int
    price: Decimal


class BookingSeatCreate(BookingSeatBase):
    pass


class BookingSeatUpdate(BaseModel):
    booking_id: Optional[int] = None
    seat_id: Optional[int] = None
    price: Optional[Decimal] = None


class BookingSeatResponse(BookingSeatBase):
    id: int

    class Config:
        from_attributes = True