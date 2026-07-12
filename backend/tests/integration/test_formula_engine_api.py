from fastapi.testclient import TestClient

from app.main import app


def test_formula_engine_internal_api_evaluates_formula() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/kpi/internal/formulas/evaluate",
        json={
            "formula_id": "revenue.net",
            "company_id": "cmp_acme",
            "period_ref": "2026-07",
            "metrics": {
                "fact_sales.gross_revenue": 1000,
                "fact_sales.tax_amount": 100,
                "fact_sales.return_amount": 50,
                "fact_sales.discount_amount": 20,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["formula_id"] == "revenue.net"
    assert payload["value"] == 830.0
    assert payload["unit"] == "BRL"
    assert payload["audit"]["company_id"] == "cmp_acme"
