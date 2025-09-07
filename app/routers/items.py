from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from ..models import Item, ItemCreate, ItemUpdate
from ..models_sqlalchemy import Item as ItemDB
from ..database import get_db
from ..auth import get_current_admin

router = APIRouter(prefix="/items", tags=["items"])


@router.post("/", response_model=Item, summary="Create Item")
async def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new item"""
    db_item = ItemDB(
        name=item.name,
        unit=item.unit
    )
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return Item(
        id=str(db_item.id),
        name=db_item.name,
        unit=db_item.unit
    )

@router.get("/", response_model=List[Item], summary="Get All Items")
async def get_items(db: Session = Depends(get_db)):
    """Get all items"""
    db_items = db.query(ItemDB).all()
    
    items = []
    for item in db_items:
        items.append(Item(
            id=str(item.id),
            name=item.name,
            unit=item.unit
        ))
    
    return items

@router.get("/{item_id}", response_model=Item, summary="Get Item by ID")
async def get_item(item_id: str, db: Session = Depends(get_db)):
    """Get a specific item by ID"""
    db_item = db.query(ItemDB).filter(ItemDB.id == int(item_id)).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return Item(
        id=str(db_item.id),
        name=db_item.name,
        unit=db_item.unit
    )

@router.patch("/{item_id}", response_model=Item, summary="Update Item")
async def update_item(
    item_id: str,
    item_update: ItemUpdate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Update an item"""
    db_item = db.query(ItemDB).filter(ItemDB.id == int(item_id)).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = item_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    
    return Item(
        id=str(db_item.id),
        name=db_item.name,
        unit=db_item.unit
    )

@router.delete("/{item_id}", summary="Delete Item")
async def delete_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Delete an item"""
    db_item = db.query(ItemDB).filter(ItemDB.id == int(item_id)).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted successfully"}
