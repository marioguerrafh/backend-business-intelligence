from app.modules.integrations.application.provider_registry import ProviderRegistry
from app.modules.integrations.providers.shared.stub_provider import StubERPProvider


def test_provider_registry_resolves_provider_without_conditionals() -> None:
    registry = ProviderRegistry(
        providers={
            "omie": StubERPProvider(provider_type="omie"),
            "sap": StubERPProvider(provider_type="sap"),
        }
    )

    provider = registry.get("omie")
    assert provider.provider_type == "omie"
    assert registry.supports("sap") is True
    assert registry.supports("oracle") is False
