from app.services.payment_providers.vnpay_provider import VNPayProvider

class PaymentProviderFactory:
    providers = {
        "vnpay": VNPayProvider,
        "momo" : ""
    }

    @staticmethod
    def get_provider(provider_name: str):
        provider_name = provider_name.lower()

        if provider_name not in PaymentProviderFactory.providers:
            raise ValueError("Unsupported payment provider")

        return PaymentProviderFactory.providers[provider_name]()
