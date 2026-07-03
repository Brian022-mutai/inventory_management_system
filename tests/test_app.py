"""
tests/test_app.py

Unit tests for the Flask API routes (app.py).
Run with: pytest
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as flask_app_module
import inventory_store as store


@pytest.fixture
def client():
    flask_app_module.app.config["TESTING"] = True

    # Reset the mock database to a known state before every test.
    store.reset([
        {
            "id": 1,
            "barcode": "1111111111111",
            "product_name": "Test Chips",
            "brands": "TestBrand",
            "ingredients_text": "Potatoes, salt, oil",
            "price": 2.50,
            "stock": 10,
        },
        {
            "id": 2,
            "barcode": "2222222222222",
            "product_name": "Test Soda",
            "brands": "TestCo",
            "ingredients_text": "Water, sugar, carbon dioxide",
            "price": 1.25,
            "stock": 30,
        },
    ])

    with flask_app_module.app.test_client() as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# GET /inventory
# ---------------------------------------------------------------------------

def test_list_items(client):
    response = client.get("/inventory")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]["product_name"] == "Test Chips"


def test_get_single_item(client):
    response = client.get("/inventory/1")
    assert response.status_code == 200
    assert response.get_json()["product_name"] == "Test Chips"


def test_get_missing_item_returns_404(client):
    response = client.get("/inventory/999")
    assert response.status_code == 404
    assert "error" in response.get_json()


# ---------------------------------------------------------------------------
# POST /inventory
# ---------------------------------------------------------------------------

def test_create_item(client):
    payload = {"product_name": "New Item", "price": 9.99, "stock": 5}
    response = client.post("/inventory", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["product_name"] == "New Item"
    assert data["price"] == 9.99
    assert "id" in data

    # Confirm it actually landed in the store.
    list_response = client.get("/inventory")
    assert len(list_response.get_json()) == 3


def test_create_item_without_name_fails(client):
    response = client.post("/inventory", json={"price": 1.0})
    assert response.status_code == 400


def test_create_item_without_json_body_fails(client):
    response = client.post("/inventory", data="not json")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# PATCH /inventory/<id>
# ---------------------------------------------------------------------------

def test_update_item(client):
    response = client.patch("/inventory/1", json={"price": 3.75, "stock": 8})
    assert response.status_code == 200
    data = response.get_json()
    assert data["price"] == 3.75
    assert data["stock"] == 8
    # Untouched fields remain the same.
    assert data["product_name"] == "Test Chips"


def test_update_missing_item_returns_404(client):
    response = client.patch("/inventory/999", json={"price": 1.0})
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /inventory/<id>
# ---------------------------------------------------------------------------

def test_delete_item(client):
    response = client.delete("/inventory/1")
    assert response.status_code == 200

    follow_up = client.get("/inventory/1")
    assert follow_up.status_code == 404


def test_delete_missing_item_returns_404(client):
    response = client.delete("/inventory/999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# External API routes (mocked)
# ---------------------------------------------------------------------------

def test_search_by_barcode_success(client, monkeypatch):
    def fake_fetch(barcode):
        return {
            "barcode": barcode,
            "product_name": "Mocked Product",
            "brands": "MockBrand",
            "ingredients_text": "mock ingredients",
        }

    monkeypatch.setattr(flask_app_module, "fetch_product_by_barcode", fake_fetch)

    response = client.get("/inventory/search/barcode/12345")
    assert response.status_code == 200
    assert response.get_json()["product_name"] == "Mocked Product"


def test_search_by_barcode_not_found(client, monkeypatch):
    from external_api import ExternalAPIError

    def fake_fetch(_barcode):
        raise ExternalAPIError("No product found for barcode '12345'.")

    monkeypatch.setattr(flask_app_module, "fetch_product_by_barcode", fake_fetch)

    response = client.get("/inventory/search/barcode/12345")
    assert response.status_code == 502
    assert "error" in response.get_json()


def test_import_item_success(client, monkeypatch):
    def fake_fetch(barcode):
        return {
            "barcode": barcode,
            "product_name": "Imported Product",
            "brands": "ImportBrand",
            "ingredients_text": "imported ingredients",
        }

    monkeypatch.setattr(flask_app_module, "fetch_product_by_barcode", fake_fetch)

    response = client.post("/inventory/import/99999", json={"price": 6.5, "stock": 12})
    assert response.status_code == 201
    data = response.get_json()
    assert data["product_name"] == "Imported Product"
    assert data["price"] == 6.5
    assert data["stock"] == 12
