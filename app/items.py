"""In-memory item store — simple enough to learn with, easy to swap for a DB later."""
from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    price: float = Field(..., gt=0)


class Item(ItemCreate):
    id: int


class ItemStore:
    """Thread-unsafe in-memory store. Good enough for learning; replace with a real DB later."""

    def __init__(self) -> None:
        self._items: dict[int, Item] = {}
        self._next_id: int = 1

    def all(self) -> list[Item]:
        return list(self._items.values())

    def get(self, item_id: int) -> Item | None:
        return self._items.get(item_id)

    def create(self, payload: ItemCreate) -> Item:
        item = Item(id=self._next_id, **payload.model_dump())
        self._items[self._next_id] = item
        self._next_id += 1
        return item

    def delete(self, item_id: int) -> bool:
        if item_id not in self._items:
            return False
        del self._items[item_id]
        return True
