"""
tests/test_cli.py

Unit tests for the CLI commands (cli.py).
The underlying `requests` calls are mocked so no real Flask server or
network connection is required to run these tests.
"""

import sys
import os
from unittest.mock import patch, Mock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import cli


def _mock_response(json_data, status_code=200):
    mock_resp = Mock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    return mock_resp


@patch("cli.requests.request")
def test_cmd_list_prints_items(mock_request, capsys):
    mock_request.return_value = _mock_response([
        {"id": 1, "product_name": "Chips", "brands": "BrandA", "price": 2.5, "stock": 10}
    ])

    args = cli.build_parser().parse_args(["list"])
    args.func(args)

    captured = capsys.readouterr()
    assert "Chips" in captured.out
    assert "BrandA" in captured.out


@patch("cli.requests.request")
def test_cmd_list_empty_inventory(mock_request, capsys):
    mock_request.return_value = _mock_response([])

    args = cli.build_parser().parse_args(["list"])
    args.func(args)

    captured = capsys.readouterr()
    assert "empty" in captured.out.lower()


@patch("cli.requests.request")
def test_cmd_add_success(mock_request, capsys):
    mock_request.return_value = _mock_response(
        {"id": 5, "product_name": "New Widget", "price": 1.0, "stock": 3}, status_code=201
    )

    args = cli.build_parser().parse_args([
        "add", "--name", "New Widget", "--price", "1.0", "--stock", "3"
    ])
    args.func(args)

    captured = capsys.readouterr()
    assert "Added item [5] New Widget." in captured.out


@patch("cli.requests.request")
def test_cmd_delete_missing_item_exits(mock_request):
    mock_request.return_value = _mock_response({"error": "Item 999 not found."}, status_code=404)

    args = cli.build_parser().parse_args(["delete", "999"])
    with pytest.raises(SystemExit):
        args.func(args)


@patch("cli.requests.request")
def test_cmd_find_by_barcode(mock_request, capsys):
    mock_request.return_value = _mock_response({
        "barcode": "123", "product_name": "Found Item", "brands": "FoundBrand"
    })

    args = cli.build_parser().parse_args(["find", "--barcode", "123"])
    args.func(args)

    captured = capsys.readouterr()
    assert "Found Item" in captured.out


def test_cmd_find_without_args_exits(capsys):
    args = cli.build_parser().parse_args(["find"])
    with pytest.raises(SystemExit):
        args.func(args)

    captured = capsys.readouterr()
    assert "Provide --barcode or --name" in captured.out


@patch("cli.requests.request")
def test_connection_error_exits_gracefully(mock_request, capsys):
    import requests
    mock_request.side_effect = requests.ConnectionError()

    args = cli.build_parser().parse_args(["list"])
    with pytest.raises(SystemExit):
        args.func(args)

    captured = capsys.readouterr()
    assert "Is the Flask server running" in captured.out
