from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, engine, get_db
from app.items import Item, ItemCreate, create_item, delete_item, get_all_items, get_item

# Import models so Base.metadata knows about them before create_all
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (idempotent — skips existing tables)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="DevOps Learning API", version="0.1.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health", tags=["health"])
async def health_check():
    """Liveness probe — always returns 200 when the app is running."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

@app.get("/items", response_model=list[Item], tags=["items"])
async def list_items(db: AsyncSession = Depends(get_db)):
    """Return all items."""
    return await get_all_items(db)


@app.get("/items/{item_id}", response_model=Item, tags=["items"])
async def get_item_endpoint(item_id: int, db: AsyncSession = Depends(get_db)):
    """Return a single item by ID."""
    item = await get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED, tags=["items"])
async def create_item_endpoint(payload: ItemCreate, db: AsyncSession = Depends(get_db)):
    """Create a new item."""
    return await create_item(db, payload)


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["items"])
async def delete_item_endpoint(item_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an item by ID."""
    deleted = await delete_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
