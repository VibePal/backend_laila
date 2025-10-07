from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from app.models import OverheadCostType, OverheadCostTypeCreate, OverheadCostTypeUpdate
from app.models_sqlalchemy import OverheadCostType as OverheadCostTypeDB
from app.database import get_db
from app.auth import get_current_admin

router = APIRouter(prefix="/overhead-cost-types", tags=["overhead-cost-types"])


@router.post("/", response_model=OverheadCostType, summary="Create Overhead Cost Type")
async def create_overhead_cost_type(
    overhead_cost_type: OverheadCostTypeCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new overhead cost type"""
    db_overhead_cost_type = OverheadCostTypeDB(
        name=overhead_cost_type.name
    )
    
    db.add(db_overhead_cost_type)
    db.commit()
    db.refresh(db_overhead_cost_type)
    
    return OverheadCostType(
        id=str(db_overhead_cost_type.id),
        name=db_overhead_cost_type.name
    )

@router.get("/", response_model=List[OverheadCostType], summary="Get All Overhead Cost Types")
async def get_overhead_cost_types(db: Session = Depends(get_db)):
    """Get all overhead cost types"""
    db_overhead_cost_types = db.query(OverheadCostTypeDB).all()
    
    overhead_cost_types = []
    for overhead_cost_type in db_overhead_cost_types:
        overhead_cost_types.append(OverheadCostType(
            id=str(overhead_cost_type.id),
            name=overhead_cost_type.name
        ))
    
    return overhead_cost_types

@router.get("/{overhead_cost_type_id}", response_model=OverheadCostType, summary="Get Overhead Cost Type by ID")
async def get_overhead_cost_type(overhead_cost_type_id: str, db: Session = Depends(get_db)):
    """Get a specific overhead cost type by ID"""
    db_overhead_cost_type = db.query(OverheadCostTypeDB).filter(OverheadCostTypeDB.id == int(overhead_cost_type_id)).first()
    if not db_overhead_cost_type:
        raise HTTPException(status_code=404, detail="Overhead cost type not found")
    
    return OverheadCostType(
        id=str(db_overhead_cost_type.id),
        name=db_overhead_cost_type.name
    )

@router.patch("/{overhead_cost_type_id}", response_model=OverheadCostType, summary="Update Overhead Cost Type")
async def update_overhead_cost_type(
    overhead_cost_type_id: str,
    overhead_cost_type_update: OverheadCostTypeUpdate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Update an overhead cost type"""
    db_overhead_cost_type = db.query(OverheadCostTypeDB).filter(OverheadCostTypeDB.id == int(overhead_cost_type_id)).first()
    if not db_overhead_cost_type:
        raise HTTPException(status_code=404, detail="Overhead cost type not found")
    
    update_data = overhead_cost_type_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_overhead_cost_type, field, value)
    
    db.commit()
    db.refresh(db_overhead_cost_type)
    
    return OverheadCostType(
        id=str(db_overhead_cost_type.id),
        name=db_overhead_cost_type.name
    )

@router.delete("/{overhead_cost_type_id}", summary="Delete Overhead Cost Type")
async def delete_overhead_cost_type(
    overhead_cost_type_id: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Delete an overhead cost type"""
    db_overhead_cost_type = db.query(OverheadCostTypeDB).filter(OverheadCostTypeDB.id == int(overhead_cost_type_id)).first()
    if not db_overhead_cost_type:
        raise HTTPException(status_code=404, detail="Overhead cost type not found")
    
    db.delete(db_overhead_cost_type)
    db.commit()
    return {"message": "Overhead cost type deleted successfully"}
