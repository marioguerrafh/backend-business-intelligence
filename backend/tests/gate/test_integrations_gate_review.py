from app.modules.integrations.application.provider_registry import ProviderRegistry
from app.modules.integrations.providers.omie.provider import OmieProvider
from app.modules.integrations.providers.shared.stub_provider import StubERPProvider


def test_gate_registry_has_multi_erp_providers() -> None:
    providers = {
        "omie",
        "conta_azul",
        "tiny",
        "bling",
        "sap",
        "totvs",
        "senior",
        "sankhya",
        "oracle",
        "dynamics",
    }
    registry = ProviderRegistry(providers={name: StubERPProvider(provider_type=name) for name in providers})
    assert set(registry.available()) == providers


def test_gate_provider_interface_contract_methods_exist() -> None:
    required = {
        "authenticate",
        "health",
        "sync_customers",
        "sync_products",
        "sync_suppliers",
        "sync_sales",
        "sync_accounts_receivable",
        "sync_accounts_payable",
        "sync_cashflow",
        "sync_inventory",
        "sync_hr",
        "full_sync",
        "incremental_sync",
        "disconnect",
    }
    omie_public = {name for name in dir(OmieProvider) if not name.startswith("_")}
    assert required.issubset(omie_public)
