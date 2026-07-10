import pytest
from fastapi import HTTPException

from app.shared.interfaces.api.tenant_guard import TenantGuard


def test_assert_payload_company_allows_same_company() -> None:
    TenantGuard.assert_payload_company("cmp_a", "cmp_a")


def test_assert_payload_company_denies_other_company() -> None:
    with pytest.raises(HTTPException) as exc:
        TenantGuard.assert_payload_company("cmp_a", "cmp_b")

    assert exc.value.status_code == 403


def test_assert_path_company_denies_other_company() -> None:
    with pytest.raises(HTTPException) as exc:
        TenantGuard.assert_path_company("cmp_a", "cmp_b")

    assert exc.value.status_code == 403
