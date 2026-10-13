"""API integration tests — exercises the full HTTP stack via FastAPI TestClient."""
import pytest
from fastapi.testclient import TestClient

from app.main import app, store


@pytest.fixture(autouse=True)
def reset_store() -> None:
    """Wipe the in-memory store before every test so tests are independent."""
    store._items.clear()
    store._next_id = 1


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# GET /items — empty
# ---------------------------------------------------------------------------

def test_list_items_empty(client: TestClient) -> None:
    response = client.get("/items")
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# POST /items
# ---------------------------------------------------------------------------

def test_create_item_returns_201(client: TestClient) -> None:
    payload = {"name": "Widget", "description": "A widget", "price": 9.99}
    response = client.post("/items", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["name"] == "Widget"
    assert body["price"] == 9.99


def test_create_item_missing_name_returns_422(client: TestClient) -> None:
    response = client.post("/items", json={"price": 5.0})
    assert response.status_code == 422


def test_create_item_invalid_price_returns_422(client: TestClient) -> None:
    response = client.post("/items", json={"name": "X", "price": -1.0})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /items/{id}
# ---------------------------------------------------------------------------

def test_get_item_returns_correct_item(client: TestClient) -> None:
    client.post("/items", json={"name": "Gadget", "price": 19.99})
    response = client.get("/items/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Gadget"


def test_get_item_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/items/999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /items/{id}
# ---------------------------------------------------------------------------

def test_delete_item_returns_204(client: TestClient) -> None:
    client.post("/items", json={"name": "Temp", "price": 1.0})
    response = client.delete("/items/1")
    assert response.status_code == 204


def test_delete_item_removes_it_from_list(client: TestClient) -> None:
    client.post("/items", json={"name": "Temp", "price": 1.0})
    client.delete("/items/1")
    response = client.get("/items")
    assert response.json() == []


def test_delete_item_not_found_returns_404(client: TestClient) -> None:
    response = client.delete("/items/999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Full round-trip
# ---------------------------------------------------------------------------

def test_full_crud_round_trip(client: TestClient) -> None:
    # create two items
    r1 = client.post("/items", json={"name": "A", "price": 1.0})
    r2 = client.post("/items", json={"name": "B", "price": 2.0})
    assert r1.status_code == 201
    assert r2.status_code == 201

    # list should have both
    items = client.get("/items").json()
    assert len(items) == 2

    # delete one, list should have one left
    client.delete(f"/items/{r1.json()['id']}")
    items = client.get("/items").json()
    assert len(items) == 1
    assert items[0]["name"] == "B"
