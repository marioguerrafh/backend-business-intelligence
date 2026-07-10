from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login(email: str, password: str, company_id: str) -> dict[str, str | int]:
    response = client.post(
        "/v1/auth/login",
        json={"email": email, "password": password, "company_id": company_id},
    )
    assert response.status_code == 200
    return response.json()


def test_login_and_me_success() -> None:
    tokens = _login("owner@acme.com", "Owner@123", "cmp_acme")

    me = client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert me.status_code == 200
    payload = me.json()
    assert payload["company_id"] == "cmp_acme"
    assert "owner" in payload["roles"]


def test_refresh_and_old_token_reuse_is_denied() -> None:
    tokens = _login("owner@acme.com", "Owner@123", "cmp_acme")

    refresh = client.post("/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh.status_code == 200
    rotated = refresh.json()

    assert rotated["refresh_token"] != tokens["refresh_token"]

    reused = client.post("/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert reused.status_code == 401


def test_rbac_admin_can_list_company_users() -> None:
    tokens = _login("owner@acme.com", "Owner@123", "cmp_acme")

    response = client.get(
        "/v1/auth/users",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 200
    users = response.json()
    assert any(user["email"] == "owner@acme.com" for user in users)


def test_rbac_analyst_cannot_list_company_users() -> None:
    tokens = _login("analyst@acme.com", "Analyst@123", "cmp_acme")

    response = client.get(
        "/v1/auth/users",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 403


def test_tenant_membership_enforced_in_login() -> None:
    response = client.post(
        "/v1/auth/login",
        json={"email": "analyst@acme.com", "password": "Analyst@123", "company_id": "cmp_omega"},
    )

    assert response.status_code == 401
