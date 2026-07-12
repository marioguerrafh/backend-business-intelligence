from __future__ import annotations

from typing import Any, Protocol


class KpiCatalogReader(Protocol):
    def load_kpis(self) -> dict[str, dict[str, Any]]:
        raise NotImplementedError
