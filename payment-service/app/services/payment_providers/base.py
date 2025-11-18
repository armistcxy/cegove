# payment_providers/base.py
from abc import ABC, abstractmethod

class PaymentProvider(ABC):
    
    @abstractmethod
    def extract_payment_id(self, params: dict) -> int:
        pass

    @abstractmethod
    def verify_ipn(self, params: dict) -> bool:
        pass

    @abstractmethod
    def is_success(self, params: dict) -> bool:
        pass

    @abstractmethod
    def build_payment_url(self, payment_id: int, amount: float, ip: str) -> str:
        pass