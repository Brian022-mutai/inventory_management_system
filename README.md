# Inventory Management System

A Flask-based REST API and CLI for managing retail inventory, with
integration into the [OpenFoodFacts API](https://world.openfoodfacts.org/data)
to supplement product details (name, brand, ingredients) by barcode or
product name.

Built for a small retail company as an administrator portal: employees can
add, view, update, and delete inventory items, and pull real product data
in instead of typing it all by hand.

## Project Structure

```
inventory-management-system/
├── app.py                  # Flask REST API (routes/CRUD)
├── inventory_store.py      # In-memory mock "database" (array of items)
├── external_api.py         # OpenFoodFacts API integration
├── cli.py                  # Command-line interface (talks to the API)
├── requirements.txt
├── tests/
│   ├── test_app.py             # Flask route tests
│   ├── test_external_api.py    # External API tests (mocked with unittest.mock)
│   └── test_cli.py             # CLI tests (mocked)
└── README.md
```

## Installation and Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/inventory-management-system.git
   cd inventory-management-system
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run the Flask API:
   ```bash
   flask --app app run
   # or: python app.py
   ```
   The API will be available at `http://127.0.0.1:5000`.

4. In a separate terminal (with the API still running), use the CLI:
   ```bash
   python cli.py list
   ```

## API Endpoint Details

| Method | Endpoint                                | Description                                     |
|--------|------------------------------------------|--------------------------------------------------|
| GET    | `/inventory`                             | Fetch all inventory items                        |
| GET    | `/inventory/<id>`                        | Fetch a single item by id                         |
| POST   | `/inventory`                             | Create a new item (JSON body)                     |
| PATCH  | `/inventory/<id>`                        | Update an existing item (partial JSON body)        |
| DELETE | `/inventory/<id>`                        | Delete an item by id                              |
| GET    | `/inventory/search/barcode/<barcode>`    | Look up a product on OpenFoodFacts by barcode      |
| GET    | `/inventory/search/name/<name>`          | Look up products on OpenFoodFacts by name          |
| POST   | `/inventory/import/<barcode>`            | Fetch a product from OpenFoodFacts and add it directly to inventory (optional `price`/`stock` in JSON body) |

### Example item JSON

```json
{
  "id": 1,
  "barcode": "3017620422003",
  "product_name": "Nutella",
  "brands": "Ferrero",
  "ingredients_text": "Sugar, palm oil, hazelnuts, cocoa, milk, ...",
  "price": 4.99,
  "stock": 25
}
```

### Example requests

```bash
# List everything
curl http://127.0.0.1:5000/inventory

# Add an item manually
curl -X POST http://127.0.0.1:5000/inventory \
  -H "Content-Type: application/json" \
  -d '{"product_name": "Oat Milk", "brands": "Oatly", "price": 3.99, "stock": 20}'

# Update price/stock
curl -X PATCH http://127.0.0.1:5000/inventory/1 \
  -H "Content-Type: application/json" \
  -d '{"price": 4.49, "stock": 15}'

# Delete an item
curl -X DELETE http://127.0.0.1:5000/inventory/1

# Search OpenFoodFacts by barcode
curl http://127.0.0.1:5000/inventory/search/barcode/3017620422003

# Import a product straight from OpenFoodFacts into inventory
curl -X POST http://127.0.0.1:5000/inventory/import/3017620422003 \
  -H "Content-Type: application/json" \
  -d '{"price": 5.99, "stock": 10}'
```

## CLI Usage

The CLI is a thin client over the REST API, so the Flask server must be
running first.

```bash
# List all inventory items
python cli.py list

# View a single item
python cli.py view 1

# Add a new item
python cli.py add --name "Oat Milk" --brand "Oatly" --price 3.99 --stock 20

# Update price and/or stock (or name/brand)
python cli.py update 1 --price 4.49 --stock 15

# Delete an item
python cli.py delete 1

# Find a product on OpenFoodFacts by barcode or name
python cli.py find --barcode 3017620422003
python cli.py find --name "chocolate"

# Import a product from OpenFoodFacts directly into inventory
python cli.py import 3017620422003 --price 5.99 --stock 10
```

All commands print a clear error message and exit non-zero on failure
(invalid input, item not found, API unreachable, etc.) instead of
crashing with a raw traceback.

## Running Tests

```bash
pytest
```

This runs three test suites:
- `tests/test_app.py` — Flask route/CRUD tests (using Flask's test client)
- `tests/test_external_api.py` — OpenFoodFacts integration tests, with all
  network calls mocked via `unittest.mock`
- `tests/test_cli.py` — CLI command tests, with all `requests` calls mocked

## Design Notes

- Inventory is stored in a simple in-memory array (`inventory_store.py`)
  rather than a real database, per the lab's "simulated data storage"
  requirement. Every item has a unique auto-incrementing `id`.
- The external API integration (`external_api.py`) normalizes
  OpenFoodFacts' nested `product` JSON into a flat dict matching the shape
  used internally, so imported items look the same as manually-added ones.
- The CLI never talks to OpenFoodFacts directly — it always goes through
  the Flask API, keeping a single source of truth for inventory data and
  a clean separation between frontend (CLI) and backend (Flask + external API).

## Maintenance

- Run `pytest` before pushing any change.
- New routes should follow the existing RESTful conventions
  (`/inventory`, `/inventory/<id>`) and return JSON with appropriate
  HTTP status codes.
- Keep `external_api.py` as the only module that imports `requests`
  for outbound OpenFoodFacts calls, so API changes stay isolated to one file.
