from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from app.models import Supplier, SupplierCreate, SupplierUpdate
from app.models_sqlalchemy import Supplier as SupplierDB
from app.database import get_db
from app.auth import get_current_admin

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.post("/", response_model=Supplier, summary="Create Supplier")
async def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new supplier"""
    db_supplier = SupplierDB(
        name=supplier.name,
        contact=supplier.contact,
        address=supplier.address
    )
    
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    
    return Supplier(
        id=str(db_supplier.id),
        name=db_supplier.name,
        contact=db_supplier.contact,
        address=db_supplier.address
    )

@router.get("/", response_model=List[Supplier], summary="Get All Suppliers")
async def get_suppliers(db: Session = Depends(get_db)):
    """Get all suppliers"""
    db_suppliers = db.query(SupplierDB).all()
    
    suppliers = []
    for supplier in db_suppliers:
        suppliers.append(Supplier(
            id=str(supplier.id),
            name=supplier.name,
            contact=supplier.contact,
            address=supplier.address
        ))
    
    return suppliers

@router.get("/{supplier_id}", response_model=Supplier, summary="Get Supplier by ID")
async def get_supplier(supplier_id: str, db: Session = Depends(get_db)):
    """Get a specific supplier by ID"""
    db_supplier = db.query(SupplierDB).filter(SupplierDB.id == int(supplier_id)).first()
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return Supplier(
        id=str(db_supplier.id),
        name=db_supplier.name,
        contact=db_supplier.contact,
        address=db_supplier.address
    )

@router.patch("/{supplier_id}", response_model=Supplier, summary="Update Supplier")
async def update_supplier(
    supplier_id: str,
    supplier_update: SupplierUpdate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Update a supplier"""
    db_supplier = db.query(SupplierDB).filter(SupplierDB.id == int(supplier_id)).first()
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    update_data = supplier_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_supplier, field, value)
    
    db.commit()
    db.refresh(db_supplier)
    
    return Supplier(
        id=str(db_supplier.id),
        name=db_supplier.name,
        contact=db_supplier.contact,
        address=db_supplier.address
    )

@router.delete("/{supplier_id}", summary="Delete Supplier")
async def delete_supplier(
    supplier_id: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Delete a supplier"""
    db_supplier = db.query(SupplierDB).filter(SupplierDB.id == int(supplier_id)).first()
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    db.delete(db_supplier)
    db.commit()
    return {"message": "Supplier deleted successfully"}
