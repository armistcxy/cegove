from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.schema.payment import PaymentCreate
from app.database.models import Payment

class PaymentRepository:
    # Post
    async def create_payment(self, db: AsyncSession, data: PaymentCreate) -> Payment:
        payment_data = data.model_dump()

        db_payment = Payment(**payment_data)

        try:
            db.add(db_payment)

            await db.commit()

            await db.refresh(db_payment)

            return db_payment
        
        except Exception as e:
            await db.rollback()
            print(f"Database transaction failed during payment creation. Rolling back. Error: {e}")
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
    


