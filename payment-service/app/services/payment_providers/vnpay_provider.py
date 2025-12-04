from app.services.payment_providers.base import PaymentProvider
from app.services.payment_providers.provider_factory import PaymentProviderFactory
from app.core.config import settings

import urllib
import hmac
import hashlib
import httpx
from datetime import datetime, timezone, timedelta

class VNPayProvider(PaymentProvider):
    def __init__(self):
        self.tmn_code = settings.VNPAY_TMN_CODE
        self.secret_key = settings.VNPAY_HASH_SECRET
        self.payment_url = settings.VNPAY_PAYMENT_URL
        self.return_url = settings.VNPAY_RETURN_URL
        self.ipn_url = settings.VNPAY_IPN_URL
        self.query_url = settings.VNPAY_QUERY_URL
    
    def extract_payment_id(self, params: dict) -> int:
        return int(params["vnp_TxnRef"])

    def is_success(self, params: dict) -> bool:
        return params.get("vnp_ResponseCode") == "00"

    def verify_ipn(self, params: dict) -> bool:
        # Required by VNPay: Do NOT include vnp_SecureHash
        received_hash = params.get("vnp_SecureHash")

        params_for_hash = {
            k: v for k, v in params.items()
            if k != "vnp_SecureHash"
        }

        sorted_query = urllib.parse.urlencode(sorted(params_for_hash.items()))

        valid_hash = hmac.new(
            self.secret_key.encode(),
            sorted_query.encode(),
            hashlib.sha512,
        ).hexdigest()

        return received_hash == valid_hash

    def build_payment_url(self, payment_id: int, amount: float, ip: str):
        vn_tz = timezone(timedelta(hours=7))
        create_date = datetime.now(vn_tz)
        expire_date = create_date + timedelta(minutes=15)
        
        params = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_TmnCode": self.tmn_code,
            "vnp_Amount": int(amount * 100),
            "vnp_CurrCode": "VND",
            "vnp_TxnRef": str(payment_id),
            "vnp_OrderInfo": f"Thanh toan don hang {payment_id}",
            "vnp_OrderType": "billpayment",
            "vnp_Locale": "vn",
            "vnp_IpAddr": ip,
            "vnp_ReturnUrl": self.return_url,
            "vnp_CreateDate": create_date.strftime("%Y%m%d%H%M%S"),
            "vnp_ExpireDate": expire_date.strftime("%Y%m%d%H%M%S"),
        }

        sorted_query = urllib.parse.urlencode(sorted(params.items()))

        secure_hash = hmac.new(
            self.secret_key.encode(),
            sorted_query.encode(),
            hashlib.sha512,
        ).hexdigest()

        payment_url = f"{self.payment_url}?{sorted_query}&vnp_SecureHash={secure_hash}&vnp_SecureHashType=HMACSHA512"
        
        # Debug: print URL and key info
        print("=" * 80)
        print(f"TMN_CODE: {self.tmn_code}")
        print(f"SECRET (first 4 chars): {self.secret_key[:4]}...")
        print(f"CreateDate: {create_date.strftime('%Y%m%d%H%M%S')}")
        print(f"ExpireDate: {expire_date.strftime('%Y%m%d%H%M%S')}")
        print(f"Payment URL: {payment_url}")
        print("=" * 80)
        
        return payment_url

    async def query_payment(self, payment_id: int, transaction_date: str, request_id: str = None) -> dict:
        """
        Query VNPay to check payment status
        transaction_date format: YYYYMMDDHHmmss (e.g., "20231204151134")
        """
        vn_tz = timezone(timedelta(hours=7))
        create_date = datetime.now(vn_tz).strftime("%Y%m%d%H%M%S")
        
        # Generate unique request ID if not provided
        if not request_id:
            request_id = create_date + str(payment_id)
        
        # Build hash data according to VNPay spec
        hash_data = "|".join([
            request_id,
            "2.1.0",
            "querydr",
            self.tmn_code,
            str(payment_id),
            transaction_date,
            create_date,
            "127.0.0.1",
            f"Query payment {payment_id}"
        ])
        
        secure_hash = hmac.new(
            self.secret_key.encode(),
            hash_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        payload = {
            "vnp_RequestId": request_id,
            "vnp_Version": "2.1.0",
            "vnp_Command": "querydr",
            "vnp_TmnCode": self.tmn_code,
            "vnp_TxnRef": str(payment_id),
            "vnp_OrderInfo": f"Query payment {payment_id}",
            "vnp_TransactionDate": transaction_date,
            "vnp_CreateDate": create_date,
            "vnp_IpAddr": "127.0.0.1",
            "vnp_SecureHash": secure_hash
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.query_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                result = response.json()
                
                print("=" * 80)
                print(f"VNPay Query Response: {result}")
                print("=" * 80)
                
                return result
        except Exception as e:
            print(f"Error querying VNPay: {e}")
            return {}

