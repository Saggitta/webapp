"""Unit tests for Pydantic schemas in app/items.py.

ItemStore is gone — these tests cover the validation rules on ItemCreate
and the ORM-mode behaviour of Item.
"""
import pytest

from app.items import Item, ItemCreate


# ---------------------------------------------------------------------------
# ItemCreate — valid inputs
# ---------------------------------------------------------------------------

def test_item_create_accepts_valid_payload() -> None:
    item = ItemCreate(name="Widget", description="A widget", price=9.99)
    assert item.name == "Widget"
    assert item.price == 9.99


def test_item_create_description_defaults_to_empty_string() -> None:
    item = ItemCreate(name="Widget", price=1.0)
    assert item.description == ""


# ---------------------------------------------------------------------------
# ItemCreate — invalid inputs
# ---------------------------------------------------------------------------

def test_item_create_rejects_empty_name() -> None:
    with pytest.raises(Exception):
        ItemCreate(name="", price=1.0)


def test_item_create_rejects_name_too_long() -> None:
    with pytest.raises(Exception):
        ItemCreate(name="x" * 101, price=1.0)


def test_item_create_rejects_zero_price() -> None:
    with pytest.raises(Exception):
        ItemCreate(name="X", price=0.0)


def test_item_create_rejects_negative_price() -> None:
    with pytest.raises(Exception):
        ItemCreate(name="X", price=-5.0)


def test_item_create_rejects_description_too_long() -> None:
    with pytest.raises(Exception):
        ItemCreate(name="X", price=1.0, description="x" * 501)


# ---------------------------------------------------------------------------
# Item — ORM mode (from_attributes=True)
# ---------------------------------------------------------------------------

def test_item_can_be_built_from_orm_like_object() -> None:
    """Simulate what SQLAlchemy returns: an object with attributes."""

    class FakeRow:
        id = 42
        name = "Gadget"
        description = "cool"
        price = 19.99

    item = Item.model_validate(FakeRow())
    assert item.id == 42
    assert item.name == "Gadget"
    assert item.price == 19.99


def test_item_serialises_to_dict() -> None:
    item = Item(id=1, name="A", description="", price=5.0)
    d = item.model_dump()
    assert d == {"id": 1, "name": "A", "description": "", "price": 5.0}
