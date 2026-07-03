

import requests

BASE_URL = "https://world.openfoodfacts.org"
TIMEOUT = 10  # seconds


class ExternalAPIError(Exception):
    """Raised when the OpenFoodFacts API can't be reached or returns bad data."""
    pass


def fetch_product_by_barcode(barcode):
    """
    Look up a single product by barcode (UPC/EAN code).

    Returns a normalized dict:
        {
            "barcode": str,
            "product_name": str,
            "brands": str,
            "ingredients_text": str,
        }

    Raises ExternalAPIError if the request fails or the product isn't found.
    """
    url = f"{BASE_URL}/api/v2/product/{barcode}.json"

    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ExternalAPIError(f"Could not reach OpenFoodFacts API: {exc}") from exc

    data = response.json()

    if data.get("status") != 1:
        raise ExternalAPIError(f"No product found for barcode '{barcode}'.")

    product = data.get("product", {})
    return {
        "barcode": barcode,
        "product_name": product.get("product_name", "Unknown product"),
        "brands": product.get("brands", ""),
        "ingredients_text": product.get("ingredients_text", ""),
    }


def search_products_by_name(name, page_size=5):
    """
    Search OpenFoodFacts for products matching a text query (product name).

    Returns a list of normalized dicts (same shape as fetch_product_by_barcode,
    minus a guaranteed barcode -- it's taken from the "code" field when present).

    Raises ExternalAPIError if the request fails.
    """
    url = f"{BASE_URL}/cgi/search.pl"
    params = {
        "search_terms": name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": page_size,
    }

    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ExternalAPIError(f"Could not reach OpenFoodFacts API: {exc}") from exc

    data = response.json()
    products = data.get("products", [])

    results = []
    for product in products:
        results.append({
            "barcode": product.get("code", ""),
            "product_name": product.get("product_name", "Unknown product"),
            "brands": product.get("brands", ""),
            "ingredients_text": product.get("ingredients_text", ""),
        })

    if not results:
        raise ExternalAPIError(f"No products found matching '{name}'.")

    return results
