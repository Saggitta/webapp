"""Unit tests for ItemStore — no HTTP, no FastAPI, pure logic."""
import pytest

from app.items import Item, ItemCreate, ItemStore


@pytest.fixture()
def store() -> ItemStore:
    """Fresh store for every test."""
    return ItemStore()


@pytest.fixture()
def populated_store(store: ItemStore) -> ItemStore:
    store.create(ItemCreate(name="Widget", description="A small widget", price=9.99))
    store.create(ItemCreate(name="Gadget", description="A cool gadget", price=24.99))
    return store


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

def test_create_returns_item_with_id(store: ItemStore) -> None:
    payload = ItemCreate(name="Widget", description="desc", price=5.0)
    item = store.create(payload)
    assert isinstance(item, Item)
    assert item.id == 1
    assert item.name == "Widget"
    assert item.price == 5.0


def test_create_auto_increments_id(store: ItemStore) -> None:
    item1 = store.create(ItemCreate(name="A", price=1.0))
    item2 = store.create(ItemCreate(name="B", price=2.0))
    assert item2.id == item1.id + 1


# ---------------------------------------------------------------------------
# all
# ---------------------------------------------------------------------------

def test_all_returns_empty_list_initially(store: ItemStore) -> None:
    assert store.all() == []


def test_all_returns_all_created_items(populated_store: ItemStore) -> None:
    items = populated_store.all()
    assert len(items) == 2
    names = {i.name for i in items}
    assert names == {"Widget", "Gadget"}


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

def test_get_returns_correct_item(populated_store: ItemStore) -> None:
    item = populated_store.get(1)
    assert item is not None
    assert item.name == "Widget"


def test_get_returns_none_for_missing_id(store: ItemStore) -> None:
    assert store.get(999) is None


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

def test_delete_removes_item(populated_store: ItemStore) -> None:
    result = populated_store.delete(1)
    assert result is True
    assert populated_store.get(1) is None


def test_delete_returns_false_for_missing_id(store: ItemStore) -> None:
    assert store.delete(999) is False


def test_delete_does_not_affect_other_items(populated_store: ItemStore) -> None:
    populated_store.delete(1)
    remaining = populated_store.all()
    assert len(remaining) == 1
    assert remaining[0].name == "Gadget"


# ---------------------------------------------------------------------------
# Pydantic validation
# ---------------------------------------------------------------------------

def test_item_create_rejects_empty_name() -> None:
    with pytest.raises(Exception):
        ItemCreate(name="", price=1.0)


def test_item_create_rejects_zero_price() -> None:
    with pytest.raises(Exception):
        ItemCreate(name="X", price=0.0)


def test_item_create_rejects_negative_price() -> None:
    with pytest.raises(Exception):
        ItemCreate(name="X", price=-5.0)
