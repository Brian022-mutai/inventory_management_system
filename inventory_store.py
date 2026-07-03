

from itertools import count
from threading import Lock

_id_counter = count(1)
_lock = Lock()


def _next_id():
    with _lock:
        return next(_id_counter)


# Seed data so the API/CLI have something to interact with out of the box.
INVENTORY = [
    {
        "id": _next_id(),
        "barcode": "3017620422003",
        "product_name": "Nutella",
        "brands": "Ferrero",
        "ingredients_text": "Sugar, palm oil, hazelnuts, cocoa, milk, ...",
        "price": 4.99,
        "stock": 25,
    },
    {
        "id": _next_id(),
        "barcode": "0025293001165",
        "product_name": "Organic Almond Milk",
        "brands": "Silk",
        "ingredients_text": "Filtered water, almonds, cane sugar, ...",
        "price": 3.49,
        "stock": 40,
    },
    {
        "id": _next_id(),
        "barcode": "5449000000996",
        "product_name": "Coca-Cola",
        "brands": "Coca-Cola",
        "ingredients_text": "Carbonated water, sugar, caramel color, ...",
        "price": 1.99,
        "stock": 100,
    },
]


def get_all_items():
    """Return every item currently in the mock database."""
    return INVENTORY


def get_item(item_id):
    """Return a single item by id, or None if not found."""
    return next((item for item in INVENTORY if item["id"] == item_id), None)


def add_item(data):
    """
    Add a new item to the mock database.

    `data` is a dict that may contain: barcode, product_name, brands,
    ingredients_text, price, stock. Missing fields default sensibly.
    Returns the newly created item (with its assigned id).
    """
    new_item = {
        "id": _next_id(),
        "barcode": data.get("barcode", ""),
        "product_name": data.get("product_name", "Unnamed Product"),
        "brands": data.get("brands", ""),
        "ingredients_text": data.get("ingredients_text", ""),
        "price": float(data.get("price", 0.0)),
        "stock": int(data.get("stock", 0)),
    }
    INVENTORY.append(new_item)
    return new_item


def update_item(item_id, data):
    """
    Update an existing item (partial update / PATCH semantics).
    Returns the updated item, or None if the item does not exist.
    """
    item = get_item(item_id)
    if item is None:
        return None

    for field in ("barcode", "product_name", "brands", "ingredients_text"):
        if field in data:
            item[field] = data[field]

    if "price" in data:
        item["price"] = float(data["price"])
    if "stock" in data:
        item["stock"] = int(data["stock"])

    return item


def delete_item(item_id):
    """Delete an item by id. Returns True if deleted, False if not found."""
    item = get_item(item_id)
    if item is None:
        return False
    INVENTORY.remove(item)
    return True


def reset(seed_items=None):
    """
    Helper used by tests to reset the in-memory store to a known state.
    """
    global INVENTORY
    INVENTORY = seed_items if seed_items is not None else []
