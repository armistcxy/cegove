from app.repositories.payment_repository import PaymentRepository
from app.schema.payment import PaymentCreate
from sqlalchemy.ext.asyncio import AsyncSession

class PaymentService:
    def __init__(self):
        self.repo = PaymentRepository()
    
    async def create_payment(self, db: AsyncSession, data: PaymentCreate):
        return await self.repo.create_payment(db, data)

    async def get_payment(self, db: AsyncSession, payment_id: int):
        return await self.repo.get_payment_by_id(db, payment_id)
    
    async def list_payment(self, db: AsyncSession, page: int, per_page: int):
        return await self.repo.get_payment_list(db, page, per_page)