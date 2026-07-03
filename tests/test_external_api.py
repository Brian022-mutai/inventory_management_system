"""
tests/test_external_api.py

Unit tests for external_api.py, using unittest.mock to simulate
OpenFoodFacts API responses (no real network calls made).
"""

import sys
import os
from unittest.mock import patch, Mock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from external_api import (
    ExternalAPIError,
    fetch_product_by_barcode,
    search_products_by_name,
)


def _mock_response(json_data, status_code=200, raise_for_status_error=None):
    mock_resp = Mock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    if raise_for_status_error:
        mock_resp.raise_for_status.side_effect = raise_for_status_error
    else:
        mock_resp.raise_for_status.return_value = None
    return mock_resp


@patch("external_api.requests.get")
def test_fetch_product_by_barcode_success(mock_get):
    mock_get.return_value = _mock_response({
        "status": 1,
        "product": {
            "product_name": "Nutella",
            "brands": "Ferrero",
            "ingredients_text": "Sugar, palm oil, hazelnuts",
        },
    })

    result = fetch_product_by_barcode("3017620422003")

    assert result["product_name"] == "Nutella"
    assert result["brands"] == "Ferrero"
    assert result["barcode"] == "3017620422003"
    mock_get.assert_called_once()


@patch("external_api.requests.get")
def test_fetch_product_by_barcode_not_found(mock_get):
    mock_get.return_value = _mock_response({"status": 0})

    with pytest.raises(ExternalAPIError):
        fetch_product_by_barcode("0000000000000")


@patch("external_api.requests.get")
def test_fetch_product_by_barcode_network_error(mock_get):
    import requests
    mock_get.side_effect = requests.ConnectionError("no network")

    with pytest.raises(ExternalAPIError):
        fetch_product_by_barcode("3017620422003")


@patch("external_api.requests.get")
def test_search_products_by_name_success(mock_get):
    mock_get.return_value = _mock_response({
        "products": [
            {"code": "111", "product_name": "Chocolate Bar", "brands": "BrandA", "ingredients_text": "cocoa, sugar"},
            {"code": "222", "product_name": "Chocolate Milk", "brands": "BrandB", "ingredients_text": "milk, cocoa"},
        ]
    })

    results = search_products_by_name("chocolate")

    assert len(results) == 2
    assert results[0]["product_name"] == "Chocolate Bar"
    assert results[1]["barcode"] == "222"


@patch("external_api.requests.get")
def test_search_products_by_name_no_results(mock_get):
    mock_get.return_value = _mock_response({"products": []})

    with pytest.raises(ExternalAPIError):
        search_products_by_name("nonexistentproductxyz")
