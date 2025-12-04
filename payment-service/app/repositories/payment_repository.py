from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.schema.payment import PaymentCreate
from app.database.models import Payment

class PaymentRepository:
    # Post
    async def create_payment(self, db: AsyncSession, data: PaymentCreate) -> Payment:
        # print("=" * 100, "payment_repository.py:create_payment")
        payment_data = {
            "booking_id": data.booking_id,
            "provider": data.provider,
            "amount": data.amount,
            "status": "pending"
        }
        # print("=" * 100, "payment_repository.py:DB CREATE")
        # print(payment_data)
        db_payment = Payment(**payment_data)

        # print(db_payment)
        # print("DB Payment details:")
        # print(f"  id: {db_payment.id}")
        # print(f"  booking_id: {db_payment.booking_id}")
        # print(f"  provider: {db_payment.provider}")
        # print(f"  amount: {db_payment.amount}")
        # print(f"  status: {db_payment.status}")
        # print(f"  transaction_time: {db_payment.transaction_time}")
        try:
            db.add(db_payment)
            await db.commit()
            await db.refresh(db_payment)
            # print(f"AFTER COMMIT - id: {db_payment.id}, transaction_time: {db_payment.transaction_time}")
            return db_payment
        
        except Exception as e:
            await db.rollback()
            # print(f"Database transaction failed during payment creation. Rolling back. Error: {e}")
            raise

    # Get by id
    async def get_payment_by_id(self, db: AsyncSession, payment_id: int) -> Optional[Payment]:
        statement = select(Payment).where(Payment.id == payment_id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    # Get list of payment
    async def get_payment_list(self, db: AsyncSession, page: int, per_page: int):
        offset = (page - 1) * per_page
        statement = select(Payment).order_by(Payment.id).limit(per_page).offset(offset)
        result = await db.execute(statement)
        return result.scalars().all()
    


