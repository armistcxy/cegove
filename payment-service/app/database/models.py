from sqlalchemy import (
    Column, BigInteger, ForeignKey, String, Numeric, TIMESTAMP
)
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Screening(Base):
    __tablename__ = "screenings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    movie_id = Column(BigInteger, ForeignKey("movies.id"), nullable=False)
    auditorium_id = Column(BigInteger, ForeignKey("auditoriums.id"), nullable=False)

    start_time = Column(TIMESTAMP, nullable=False)
    end_time = Column(TIMESTAMP, nullable=False)

    base_price = Column(Numeric(10, 2), nullable=False)
    status = Column(String(30), nullable=False)   # scheduled, cancelled, finished

    # Relationships
    bookings = relationship("Booking", back_populates="screening")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    screening_id = Column(BigInteger, ForeignKey("screenings.id"), nullable=False)

    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(30), nullable=False)  # pending, paid, cancelled
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    screening = relationship("Screening", back_populates="bookings")
    seats = relationship("BookingSeat", back_populates="booking")
    payments = relationship("Payment", back_populates="booking")

class BookingSeat(Base):
    __tablename__ = "booking_seats"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    booking_id = Column(BigInteger, ForeignKey("bookings.id"), nullable=False)
    seat_id = Column(BigInteger, ForeignKey("seats.id"), nullable=False)

    price = Column(Numeric(10, 2), nullable=False)

    # Relationships
    booking = relationship("Booking", back_populates="seats")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    booking_id = Column(BigInteger, ForeignKey("bookings.id"), nullable=False)

    provider = Column(String(50), nullable=False)      # VNPay, MoMo, Stripe
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(30), nullable=False)        # success, failed, pending
    transaction_time = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    booking = relationship("Booking", back_populates="payments")
