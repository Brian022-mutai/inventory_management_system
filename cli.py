

import argparse
import sys

import requests

API_BASE_URL = "http://127.0.0.1:5000"
TIMEOUT = 10


def _request(method, path, **kwargs):
    """Wrapper around requests that centralizes error handling."""
    url = f"{API_BASE_URL}{path}"
    try:
        response = requests.request(method, url, timeout=TIMEOUT, **kwargs)
    except requests.ConnectionError:
        print("Error: could not connect to the API. Is the Flask server running?")
        sys.exit(1)
    except requests.RequestException as exc:
        print(f"Error: request failed: {exc}")
        sys.exit(1)

    try:
        body = response.json()
    except ValueError:
        body = {}

    if response.status_code >= 400:
        message = body.get("error", f"HTTP {response.status_code}")
        print(f"Error: {message}")
        sys.exit(1)

    return body


def cmd_list(_args):
    items = _request("GET", "/inventory")
    if not items:
        print("Inventory is empty.")
        return
    for item in items:
        print(
            f"[{item['id']}] {item['product_name']} "
            f"({item.get('brands', 'N/A')}) - "
            f"${item['price']:.2f} - stock: {item['stock']}"
        )


def cmd_view(args):
    item = _request("GET", f"/inventory/{args.id}")
    for key, value in item.items():
        print(f"{key}: {value}")


def cmd_add(args):
    payload = {
        "product_name": args.name,
        "brands": args.brand or "",
        "barcode": args.barcode or "",
        "ingredients_text": args.ingredients or "",
        "price": args.price,
        "stock": args.stock,
    }
    item = _request("POST", "/inventory", json=payload)
    print(f"Added item [{item['id']}] {item['product_name']}.")


def cmd_update(args):
    payload = {}
    if args.name is not None:
        payload["product_name"] = args.name
    if args.brand is not None:
        payload["brands"] = args.brand
    if args.price is not None:
        payload["price"] = args.price
    if args.stock is not None:
        payload["stock"] = args.stock

    if not payload:
        print("Nothing to update. Provide at least one of --name/--brand/--price/--stock.")
        sys.exit(1)

    item = _request("PATCH", f"/inventory/{args.id}", json=payload)
    print(f"Updated item [{item['id']}] {item['product_name']}.")


def cmd_delete(args):
    result = _request("DELETE", f"/inventory/{args.id}")
    print(result.get("message", "Deleted."))


def cmd_find(args):
    if args.barcode:
        product = _request("GET", f"/inventory/search/barcode/{args.barcode}")
        print(f"{product['product_name']} ({product.get('brands', 'N/A')}) - barcode {product['barcode']}")
    elif args.name:
        products = _request("GET", f"/inventory/search/name/{args.name}")
        for product in products:
            print(f"{product['product_name']} ({product.get('brands', 'N/A')}) - barcode {product.get('barcode', 'N/A')}")
    else:
        print("Provide --barcode or --name to search.")
        sys.exit(1)


def cmd_import(args):
    payload = {"price": args.price, "stock": args.stock}
    item = _request("POST", f"/inventory/import/{args.barcode}", json=payload)
    print(f"Imported item [{item['id']}] {item['product_name']} from OpenFoodFacts.")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="CLI for the Inventory Management System.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List all inventory items.").set_defaults(func=cmd_list)

    p_view = subparsers.add_parser("view", help="View a single inventory item.")
    p_view.add_argument("id", type=int)
    p_view.set_defaults(func=cmd_view)

    p_add = subparsers.add_parser("add", help="Add a new inventory item.")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--brand")
    p_add.add_argument("--barcode")
    p_add.add_argument("--ingredients")
    p_add.add_argument("--price", type=float, default=0.0)
    p_add.add_argument("--stock", type=int, default=0)
    p_add.set_defaults(func=cmd_add)

    p_update = subparsers.add_parser("update", help="Update price/stock/name/brand.")
    p_update.add_argument("id", type=int)
    p_update.add_argument("--name")
    p_update.add_argument("--brand")
    p_update.add_argument("--price", type=float)
    p_update.add_argument("--stock", type=int)
    p_update.set_defaults(func=cmd_update)

    p_delete = subparsers.add_parser("delete", help="Delete an inventory item.")
    p_delete.add_argument("id", type=int)
    p_delete.set_defaults(func=cmd_delete)

    p_find = subparsers.add_parser("find", help="Find a product on OpenFoodFacts.")
    p_find.add_argument("--barcode")
    p_find.add_argument("--name")
    p_find.set_defaults(func=cmd_find)

    p_import = subparsers.add_parser("import", help="Import a product from OpenFoodFacts into inventory.")
    p_import.add_argument("barcode")
    p_import.add_argument("--price", type=float, default=0.0)
    p_import.add_argument("--stock", type=int, default=0)
    p_import.set_defaults(func=cmd_import)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
