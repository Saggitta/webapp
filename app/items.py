"""Pydantic schemas and async CRUD functions for items."""
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ItemModel


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    price: float = Field(..., gt=0)


class Item(ItemCreate):
    id: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

async def get_all_items(db: AsyncSession) -> list[Item]:
    result = await db.execute(select(ItemModel).order_by(ItemModel.id))
    return [Item.model_validate(row) for row in result.scalars()]


async def get_item(db: AsyncSession, item_id: int) -> Item | None:
    row = await db.get(ItemModel, item_id)
    return Item.model_validate(row) if row else None


async def create_item(db: AsyncSession, payload: ItemCreate) -> Item:
    row = ItemModel(**payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return Item.model_validate(row)


async def delete_item(db: AsyncSession, item_id: int) -> bool:
    row = await db.get(ItemModel, item_id)
    if row is None:
        return False
    await db.delete(row)
    await db.commit()
    return True
