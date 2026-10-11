import math

from fastapi.testclient import TestClient

import app as api
from phi_formulas import (
    FORMULA_CATEGORIES,
    compute_action,
    compute_distance,
    compute_elegance,
    compute_phi,
)


def test_public_health_and_head():
    client = TestClient(api.app)
    assert client.get("/health").status_code == 200
    assert client.get("/health").json()["status"] == "ok"
    assert client.head("/").status_code == 200


def test_protected_endpoint_requires_token(monkeypatch):
    monkeypatch.setenv("PHI_API_TOKEN", "test-secret")
    client = TestClient(api.app)
    assert client.get("/formulas").status_code == 401
    response = client.get("/formulas", headers={"Authorization": "Bearer test-secret"})
    assert response.status_code == 200
    assert response.json()["count"] == sum(map(len, FORMULA_CATEGORIES.values()))


def test_compute_endpoint_and_validation(monkeypatch):
    monkeypatch.setenv("PHI_API_TOKEN", "test-secret")
    client = TestClient(api.app)
    headers = {"Authorization": "Bearer test-secret"}
    response = client.post(
        "/compute",
        headers=headers,
        json={"operation": "elegance", "parameters": {"C": 2, "K": 0.5}},
    )
    assert response.status_code == 200
    assert response.json()["result"] == 4
    missing = client.post(
        "/compute", headers=headers,
        json={"operation": "elegance", "parameters": {"C": 2}},
    )
    assert missing.status_code == 422
    unknown = client.post(
        "/compute", headers=headers,
        json={"operation": "not-real", "parameters": {}},
    )
    assert unknown.status_code == 400


def test_formula_helpers():
    assert compute_phi([2, 3], V_P=1) == 5
    assert compute_elegance(2, 0.5) == 4
    assert compute_action(2, 1, 3, 2) == 7
    assert compute_distance(0) == math.inf
