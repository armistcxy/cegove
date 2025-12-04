from app.repositories.payment_repository import PaymentRepository
from app.schema.payment import PaymentCreate, PaymentInitResponse, PaymentOut
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.payment_providers.provider_factory import PaymentProviderFactory

class PaymentService:
    def __init__(self):
        self.repo = PaymentRepository()
    
    async def create_payment(self, db: AsyncSession, data: PaymentCreate):
        print("=" * 100)
        payment = await self.repo.create_payment(db, data)


        print(payment.provider)
        print(type(payment.provider))
        provider = PaymentProviderFactory.get_provider(payment.provider)
        client_ip = data.client_ip

        payment_url = provider.build_payment_url(payment.id, payment.amount, client_ip)
        payment_out = PaymentOut.model_validate(payment)

        return PaymentInitResponse(
            payment=payment_out,
            url=payment_url
        )

    
    async def get_payment(self, db: AsyncSession, payment_id: int):
        return await self.repo.get_payment_by_id(db, payment_id)
    
    async def list_payments(self, db: AsyncSession, page: int, per_page: int):
        return await self.repo.get_payment_list(db, page, per_page)
    
    async def handle_ipn(self, db, params: dict):
        payment_id_guess = params.get("vnp_TxnRef") \
                        or params.get("orderId") \
                        or params.get("apptransid")

        if not payment_id_guess:
            return "99", "Invalid request"

        payment = await self.repo.get_payment_by_id(db, int(payment_id_guess))
        if not payment:
            return "01", "Order not found"

        provider = PaymentProviderFactory.get_provider(payment.provider)

        # 2) Verify signature
        if not provider.verify_ipn(params.copy()):
            return "97", "Invalid signature"

        # 3) Extract correct payment id
        payment_id = provider.extract_payment_id(params)
        if payment_id != payment.id:
            return "04", "Invalid amount or id mismatch"

        # 4) Prevent double-update
        if payment.status == "success":
            return "02", "Order Already Updated"

        # 5) Verify amount
        amount = float(params.get("vnp_Amount", 0)) / 100
        if amount != float(payment.amount):
            return "04", "Invalid amount"

        # 6) Update payment status
        if provider.is_success(params):
            payment.status = "success"
        else:
            payment.status = "failed"

        await db.commit()

        return "00", "Confirm Success"

