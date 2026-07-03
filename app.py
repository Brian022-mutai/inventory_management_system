
from flask import Flask, jsonify, request

import inventory_store as store
from external_api import (
    ExternalAPIError,
    fetch_product_by_barcode,
    search_products_by_name,
)

app = Flask(__name__)


# CRUD routes


@app.route("/inventory", methods=["GET"])
def list_items():
    return jsonify(store.get_all_items()), 200


@app.route("/inventory/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = store.get_item(item_id)
    if item is None:
        return jsonify({"error": f"Item {item_id} not found."}), 404
    return jsonify(item), 200


@app.route("/inventory", methods=["POST"])
def create_item():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400
    if not data.get("product_name"):
        return jsonify({"error": "'product_name' is required."}), 400

    new_item = store.add_item(data)
    return jsonify(new_item), 201


@app.route("/inventory/<int:item_id>", methods=["PATCH"])
def update_item(item_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    updated = store.update_item(item_id, data)
    if updated is None:
        return jsonify({"error": f"Item {item_id} not found."}), 404
    return jsonify(updated), 200


@app.route("/inventory/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    deleted = store.delete_item(item_id)
    if not deleted:
        return jsonify({"error": f"Item {item_id} not found."}), 404
    return jsonify({"message": f"Item {item_id} deleted."}), 200


# External API (OpenFoodFacts) helper routes

@app.route("/inventory/search/barcode/<barcode>", methods=["GET"])
def search_by_barcode(barcode):
    try:
        product = fetch_product_by_barcode(barcode)
    except ExternalAPIError as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify(product), 200


@app.route("/inventory/search/name/<name>", methods=["GET"])
def search_by_name(name):
    try:
        products = search_products_by_name(name)
    except ExternalAPIError as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify(products), 200


@app.route("/inventory/import/<barcode>", methods=["POST"])
def import_item(barcode):
    """Fetch a product from OpenFoodFacts and add it to inventory in one step."""
    try:
        product = fetch_product_by_barcode(barcode)
    except ExternalAPIError as exc:
        return jsonify({"error": str(exc)}), 502

    body = request.get_json(silent=True) or {}
    product["price"] = body.get("price", 0.0)
    product["stock"] = body.get("stock", 0)

    new_item = store.add_item(product)
    return jsonify(new_item), 201



# Error handlers


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Resource not found."}), 404


@app.errorhandler(405)
def method_not_allowed(_error):
    return jsonify({"error": "Method not allowed."}), 405


if __name__ == "__main__":
    app.run(debug=True)
