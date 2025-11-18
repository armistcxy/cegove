
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class ScreeningBase(BaseModel):
    movie_id: int
    auditorium_id: int
    start_time: datetime
    end_time: datetime
    base_price: Decimal
    status: str


class ScreeningCreate(ScreeningBase):
    pass


class ScreeningUpdate(BaseModel):
    movie_id: Optional[int] = None
    auditorium_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    base_price: Optional[Decimal] = None
    status: Optional[str] = None


class ScreeningResponse(ScreeningBase):
    id: int

    class Config:
        from_attributes = True
