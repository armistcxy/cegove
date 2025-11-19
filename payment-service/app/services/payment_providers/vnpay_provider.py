from app.services.payment_providers.base import PaymentProvider
from app.services.payment_providers.provider_factory import PaymentProviderFactory
from app.core.config import settings

import urllib
import hmac
import hashlib
import datetime

class VNPayProvider(PaymentProvider):
    def __init__(self):
        self.tmn_code = settings.VNPAY_TMN_CODE
        self.secret_key = settings.VNPAY_HASH_SECRET
        self.payment_url = settings.VNPAY_PAYMENT_URL
        self.return_url = settings.VNPAY_RETURN_URL
        self.ipn_url = settings.VNPAY_IPN_URL
    
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
        params = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_TmnCode": self.tmn_code,
            "vnp_Amount": int(amount * 100),
            "vnp_CurrCode": "VND",
            "vnp_TxnRef": str(payment_id),
            "vnp_OrderInfo": f"Payment {payment_id}",
            "vnp_OrderType": "billpayment",
            "vnp_Locale": "vn",
            "vnp_IpAddr": ip,
            "vnp_ReturnUrl": self.return_url,
            "vnp_CreateDate": datetime.now().strftime("%Y%m%d%H%M%S"),
        }

        sorted_query = urllib.parse.urlencode(sorted(params.items()))

        secure_hash = hmac.new(
            self.secret_key.encode(),
            sorted_query.encode(),
            hashlib.sha512,
        ).hexdigest()

        return f"{self.payment_url}?{sorted_query}&vnp_SecureHash={secure_hash}"

