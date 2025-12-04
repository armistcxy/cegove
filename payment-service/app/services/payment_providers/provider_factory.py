class PaymentProviderFactory:
    registry = {}

    @classmethod
    def register(cls, name: str, provider_cls):
        cls.registry[name.lower()] = provider_cls

    @classmethod
    def get_provider(cls, name: str, **kwargs):
        name = name.lower()
        provider_cls = cls.registry.get(name)

        if not provider_cls:
            raise ValueError(f"Unsupported provider: {name}")

        return provider_cls(**kwargs)

