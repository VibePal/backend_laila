from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models import PackagingType, PackagingTypeCreate, PackagingTypeUpdate
from ..models_sqlalchemy import PackagingType as PackagingTypeDB
from ..database import get_db
from ..auth import get_current_staff_or_admin

router = APIRouter(prefix="/packaging-types", tags=["packaging-types"])

@router.get("/", response_model=List[PackagingType], summary="Get All Packaging Types")
async def get_packaging_types(
    isAvailable: Optional[bool] = Query(None, description="Filter by availability"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_staff_or_admin)
):
    """Get all packaging types with optional filtering"""
    query = db.query(PackagingTypeDB)
    
    # Apply filters
    if isAvailable is not None:
        # Since PackagingTypeDB doesn't have isAvailable field, we'll return all for now
        # In a real implementation, you'd add this field to the database
        pass
    
    db_packaging_types = query.all()
    
    packaging_types = []
    for packaging_type in db_packaging_types:
        packaging_types.append(PackagingType(
            id=str(packaging_type.id),
            name=packaging_type.name,
            description=packaging_type.description,
            price=packaging_type.price,
            isAvailable=True  # Default to True since field doesn't exist in DB yet
        ))
    
    return packaging_types

@router.get("/{packaging_type_id}", response_model=PackagingType, summary="Get Packaging Type by ID")
async def get_packaging_type(
    packaging_type_id: str, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_staff_or_admin)
):
    """Get a specific packaging type by ID"""
    db_packaging_type = db.query(PackagingTypeDB).filter(PackagingTypeDB.id == int(packaging_type_id)).first()
    if not db_packaging_type:
        raise HTTPException(status_code=404, detail="Packaging type not found")
    
    return PackagingType(
        id=str(db_packaging_type.id),
        name=db_packaging_type.name,
        description=db_packaging_type.description,
        price=db_packaging_type.price,
        isAvailable=True  # Default to True since field doesn't exist in DB yet
    )

@router.post("/", response_model=PackagingType, summary="Create Packaging Type")
async def create_packaging_type(
    packaging_type: PackagingTypeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_staff_or_admin)
):
    """Create a new packaging type"""
    try:
        db_packaging_type = PackagingTypeDB(
            name=packaging_type.name,
            description=packaging_type.description,
            price=packaging_type.price
        )
        
        db.add(db_packaging_type)
        db.commit()
        db.refresh(db_packaging_type)
        
        return PackagingType(
            id=str(db_packaging_type.id),
            name=db_packaging_type.name,
            description=db_packaging_type.description,
            price=db_packaging_type.price,
            isAvailable=True
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating packaging type: {str(e)}"
        )

@router.patch("/{packaging_type_id}", response_model=PackagingType, summary="Update Packaging Type")
async def update_packaging_type(
    packaging_type_id: str,
    packaging_type_update: PackagingTypeUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_staff_or_admin)
):
    """Update a packaging type"""
    db_packaging_type = db.query(PackagingTypeDB).filter(PackagingTypeDB.id == int(packaging_type_id)).first()
    if not db_packaging_type:
        raise HTTPException(status_code=404, detail="Packaging type not found")
    
    update_data = packaging_type_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_packaging_type, field, value)
    
    db.commit()
    db.refresh(db_packaging_type)
    
    return PackagingType(
        id=str(db_packaging_type.id),
        name=db_packaging_type.name,
        description=db_packaging_type.description,
        price=db_packaging_type.price,
        isAvailable=True
    )

@router.delete("/{packaging_type_id}", summary="Delete Packaging Type")
async def delete_packaging_type(
    packaging_type_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_staff_or_admin)
):
    """Delete a packaging type"""
    db_packaging_type = db.query(PackagingTypeDB).filter(PackagingTypeDB.id == int(packaging_type_id)).first()
    if not db_packaging_type:
        raise HTTPException(status_code=404, detail="Packaging type not found")
    
    db.delete(db_packaging_type)
    db.commit()
    return {"message": "Packaging type deleted successfully"}