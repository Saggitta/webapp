from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from app.items import ItemStore, Item, ItemCreate

app = FastAPI(title="DevOps Learning API", version="0.1.0")

store = ItemStore()


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
async def list_items():
    """Return all items."""
    return store.all()


@app.get("/items/{item_id}", response_model=Item, tags=["items"])
async def get_item(item_id: int):
    """Return a single item by ID."""
    item = store.get(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED, tags=["items"])
async def create_item(payload: ItemCreate):
    """Create a new item."""
    return store.create(payload)


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["items"])
async def delete_item(item_id: int):
    """Delete an item by ID."""
    deleted = store.delete(item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
