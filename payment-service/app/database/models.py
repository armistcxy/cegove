from sqlalchemy import (
    Column, BigInteger, ForeignKey, String, Numeric, TIMESTAMP
)
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime


class Base(DeclarativeBase):
    pass

class Payment(Base):
    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    booking_id = Column(BigInteger, nullable=False)

    provider = Column(String(50), nullable=False)      # VNPay, MoMo, Stripe
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(30), nullable=False)        
    transaction_time = Column(TIMESTAMP, default=datetime.now())

    # booking = relationship("Booking", back_populates="payments")
