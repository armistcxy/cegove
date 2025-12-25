from app.repositories.payment_repository import PaymentRepository
from app.schema.payment import PaymentCreate, PaymentInitResponse, PaymentOut
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.payment_providers.provider_factory import PaymentProviderFactory
from app.core.config import settings
from app.database.session import AsyncSessionLocal
import httpx
import asyncio

class PaymentService:
    def __init__(self):
        self.repo = PaymentRepository()
        self.booking_webhook_url = settings.BOOKING_WEBHOOK_URL
    
    async def create_payment(self, db: AsyncSession, data: PaymentCreate):
        payment = await self.repo.create_payment(db, data)


        print(payment.provider)
        print(type(payment.provider))
        provider = PaymentProviderFactory.get_provider(payment.provider)
        client_ip = data.client_ip

        payment_url = provider.build_payment_url(payment.id, payment.amount, client_ip)
        payment_out = PaymentOut.model_validate(payment)
        
        # Schedule a delayed check for payment status
        asyncio.create_task(self.check_payment_status_delayed(payment.id))

        return PaymentInitResponse(
            payment=payment_out,
            url=payment_url
        )

    async def check_payment_status_delayed(self, payment_id: int):
        """Wait 16 minutes then check payment status"""
        print(f"Scheduling payment status check for payment {payment_id} in 16 minutes...")
        await asyncio.sleep(16 * 60)
        
        print(f"Executing delayed check for payment {payment_id}...")
        async with AsyncSessionLocal() as db:
            try:
                await self.query_and_update_payment(db, payment_id)
            except Exception as e:
                print(f"Error in delayed payment check for {payment_id}: {e}")
    
    async def get_payment(self, db: AsyncSession, payment_id: int):
        return await self.repo.get_payment_by_id(db, payment_id)
    
    async def list_payments(self, db: AsyncSession, page: int, per_page: int):
        return await self.repo.get_payment_list(db, page, per_page)
    
    async def query_and_update_payment(self, db: AsyncSession, payment_id: int):
        """Query VNPay for payment status and update database"""
        payment = await self.repo.get_payment_by_id(db, payment_id)
        if not payment:
            return None, "Payment not found"
        
        # Don't query if already successful
        if payment.status == "success":
            return payment, "Already successful"
        
        provider = PaymentProviderFactory.get_provider(payment.provider)
        
        # Get transaction date from payment record
        transaction_date = payment.transaction_time.strftime("%Y%m%d%H%M%S")
        
        # Query VNPay
        result = await provider.query_payment(payment.id, transaction_date)
        
        if not result or result.get("vnp_ResponseCode") != "00":
            return payment, f"Query failed: {result.get('vnp_Message', 'Unknown error')}"
        
        # Check transaction status
        transaction_status = result.get("vnp_TransactionStatus")
        
        if transaction_status == "00":
            payment.status = "success"
            payment_status = "SUCCESS"
        else:
            payment.status = "failed"
            payment_status = "FAILED"
        
        await db.commit()
        
        print("=" * 100)
        print(f"💳 PAYMENT QUERIED & UPDATED")
        print(f"   Payment ID: {payment.id}")
        print(f"   Booking ID: {payment.booking_id}")
        print(f"   Status: {payment_status}")
        print(f"   Transaction Status: {transaction_status}")
        print(f"   Amount: {payment.amount} VND")
        print("=" * 100)
        
        # Notify booking service
        asyncio.create_task(
            self.notify_booking_service(
                booking_id=payment.booking_id,
                payment_status=payment_status,
                transaction_id=payment.id
            )
        )
        
        return payment, "Updated successfully"
    
    async def notify_booking_service(self, booking_id: int, payment_status: str, transaction_id: int):
        """Send webhook to booking service about payment status"""
        payload = {
            "booking_id": str(booking_id),
            "payment_status": payment_status,  # "SUCCESS" or "FAILED"
            "transaction_id": str(transaction_id)
        }
        
        print("=" * 100)
        print(f"   WEBHOOK TO BOOKING SERVICE")
        print(f"   URL: {self.booking_webhook_url}")
        print(f"   Payload: {payload}")
        
        try:
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                response = await client.post(
                    self.booking_webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    print(f"   Status: SUCCESS (200)")
                    print(f"   Response: {response.text}")
                else:
                    print(f"   Status: FAILED ({response.status_code})")
                    print(f"   Response: {response.text}")
                    
        except Exception as e:
            print(f"   Status: ERROR")
            print(f"   Error: {e}")
        
        print("=" * 100)
    
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
            payment_status = "SUCCESS"
        else:
            payment.status = "failed"
            payment_status = "FAILED"

        await db.commit()

        print("=" * 100)
        print(f"   PAYMENT PROCESSED")
        print(f"   Payment ID: {payment.id}")
        print(f"   Booking ID: {payment.booking_id}")
        print(f"   Status: {payment_status}")
        print(f"   Amount: {payment.amount} VND")
        print(f"   Provider: {payment.provider}")
        print(f"   Sending webhook with data:")
        print(f"      - booking_id: {payment.booking_id}")
        print(f"      - payment_status: {payment_status}")
        print(f"      - transaction_id: {payment.id}")
        print("=" * 100)

        asyncio.create_task(
            self.notify_booking_service(
                booking_id=payment.booking_id,
                payment_status=payment_status,
                transaction_id=payment.id
            )
        )

        return "00", "Confirm Success"

