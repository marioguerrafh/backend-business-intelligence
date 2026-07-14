from app.modules.integrations.providers.shared.stub_provider import StubERPProvider


class ContaAzulProvider(StubERPProvider):
    def __init__(self) -> None:
        super().__init__(provider_type="conta_azul")
