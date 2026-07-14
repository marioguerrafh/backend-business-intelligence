from __future__ import annotations

from dataclasses import dataclass

from app.modules.integrations.application.provider_interface import ERPProvider


@dataclass(slots=True)
class ProviderRegistry:
    providers: dict[str, ERPProvider]

    def get(self, provider_type: str) -> ERPProvider:
        provider = self.providers.get(provider_type)
        if provider is None:
            raise ValueError(f"unsupported provider: {provider_type}")
        return provider

    def supports(self, provider_type: str) -> bool:
        return provider_type in self.providers

    def available(self) -> list[str]:
        return sorted(self.providers.keys())
