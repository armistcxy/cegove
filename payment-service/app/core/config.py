# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Get project root (parent of app/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    DATABASE_URL: str = ""
    VNPAY_TMN_CODE: str = "KF8OL4O4"
    VNPAY_HASH_SECRET: str = "UONRCACVD5A8NZPEBGTK0KJ8LRPWTV1W"
    VNPAY_PAYMENT_URL: str = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
    VNPAY_RETURN_URL: str = "http://localhost:8000/api/v1/webhooks/vnpay/return"
    VNPAY_IPN_URL: str = "http://localhost:8000/api/v1/webhooks/vnpay/ipn"

    # Pydantic settings format
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
