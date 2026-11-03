"""API integration tests — exercises the full HTTP stack via FastAPI TestClient.

The real PostgreSQL engine is replaced with an in-memory SQLite database so
tests run without any external services.  Each test gets a clean schema via
the `db_session` fixture.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app

# ---------------------------------------------------------------------------
# In-memory SQLite engine shared for the whole test session
# ---------------------------------------------------------------------------

SQLITE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(SQLITE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(autouse=True)
async def reset_db():
    """Drop and recreate all tables before every test for full isolation."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture()
async def client():
    """AsyncClient wired to the app with the DB dependency overridden."""
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

async def test_health_returns_200(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# GET /items — empty
# ---------------------------------------------------------------------------

async def test_list_items_empty(client: AsyncClient) -> None:
    response = await client.get("/items")
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# POST /items
# ---------------------------------------------------------------------------

async def test_create_item_returns_201(client: AsyncClient) -> None:
    payload = {"name": "Widget", "description": "A widget", "price": 9.99}
    response = await client.post("/items", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["name"] == "Widget"
    assert body["price"] == 9.99


async def test_create_item_missing_name_returns_422(client: AsyncClient) -> None:
    response = await client.post("/items", json={"price": 5.0})
    assert response.status_code == 422


async def test_create_item_invalid_price_returns_422(client: AsyncClient) -> None:
    response = await client.post("/items", json={"name": "X", "price": -1.0})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /items/{id}
# ---------------------------------------------------------------------------

async def test_get_item_returns_correct_item(client: AsyncClient) -> None:
    await client.post("/items", json={"name": "Gadget", "price": 19.99})
    response = await client.get("/items/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Gadget"


async def test_get_item_not_found_returns_404(client: AsyncClient) -> None:
    response = await client.get("/items/999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /items/{id}
# ---------------------------------------------------------------------------

async def test_delete_item_returns_204(client: AsyncClient) -> None:
    await client.post("/items", json={"name": "Temp", "price": 1.0})
    response = await client.delete("/items/1")
    assert response.status_code == 204


async def test_delete_item_removes_it_from_list(client: AsyncClient) -> None:
    await client.post("/items", json={"name": "Temp", "price": 1.0})
    await client.delete("/items/1")
    response = await client.get("/items")
    assert response.json() == []


async def test_delete_item_not_found_returns_404(client: AsyncClient) -> None:
    response = await client.delete("/items/999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Full round-trip
# ---------------------------------------------------------------------------

async def test_full_crud_round_trip(client: AsyncClient) -> None:
    r1 = await client.post("/items", json={"name": "A", "price": 1.0})
    r2 = await client.post("/items", json={"name": "B", "price": 2.0})
    assert r1.status_code == 201
    assert r2.status_code == 201

    items = (await client.get("/items")).json()
    assert len(items) == 2

    await client.delete(f"/items/{r1.json()['id']}")
    items = (await client.get("/items")).json()
    assert len(items) == 1
    assert items[0]["name"] == "B"
