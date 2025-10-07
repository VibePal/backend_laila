from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Staff, StaffCreate, StaffUpdate, MessageResponse, StaffRole
from app.models_sqlalchemy import Staff as StaffDB
from app.database import get_db
from app.auth import get_current_user, get_password_hash
from datetime import datetime

router = APIRouter(
    prefix="/staff",
    tags=["staff"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Staff, status_code=status.HTTP_201_CREATED)
async def create_staff(
    staff: StaffCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new staff member."""
    # Check if current user is admin
    if current_user.role != StaffRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create staff members"
        )
    
    # Check if username already exists
    existing_staff = db.query(StaffDB).filter(StaffDB.username == staff.username).first()
    if existing_staff:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create staff member
    db_staff = StaffDB(
        fullName=staff.fullName,
        username=staff.username,
        password=get_password_hash(staff.password),
        role=staff.role.value,
        isActive=True
    )
    
    db.add(db_staff)
    db.commit()
    db.refresh(db_staff)
    
    return Staff(
        id=str(db_staff.id),
        fullName=db_staff.fullName,
        username=db_staff.username,
        role=StaffRole(db_staff.role),
        isActive=db_staff.isActive,
        createdAt=db_staff.createdAt.isoformat()
    )

@router.get("/", response_model=List[Staff])
async def get_all_staff(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all staff members."""
    # Check if current user is admin
    if current_user.role != StaffRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view all staff members"
        )
    
    db_staff = db.query(StaffDB).all()
    
    staff_list = []
    for staff in db_staff:
        staff_list.append(Staff(
            id=str(staff.id),
            fullName=staff.fullName,
            username=staff.username,
            role=StaffRole(staff.role),
            isActive=staff.isActive,
            createdAt=staff.createdAt.isoformat()
        ))
    
    return staff_list

@router.get("/search", response_model=List[Staff])
async def search_staff(
    username: Optional[str] = Query(None, description="Search by username"),
    full_name: Optional[str] = Query(None, description="Search by full name"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Search staff members by username or full name."""
    # Check if current user is admin
    if current_user.role != StaffRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can search staff members"
        )
    
    if not username and not full_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide either username or full_name parameter"
        )
    
    query = db.query(StaffDB)
    
    # Search by username
    if username:
        query = query.filter(StaffDB.username.ilike(f"%{username}%"))
    
    # Search by full name
    if full_name:
        query = query.filter(StaffDB.fullName.ilike(f"%{full_name}%"))
    
    db_staff = query.all()
    
    results = []
    for staff in db_staff:
        results.append(Staff(
            id=str(staff.id),
            fullName=staff.fullName,
            username=staff.username,
            role=StaffRole(staff.role),
            isActive=staff.isActive,
            createdAt=staff.createdAt.isoformat()
        ))
    
    return results

@router.get("/me", response_model=Staff)
async def get_current_staff(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current staff member information."""
    # Find staff by username
    db_staff = db.query(StaffDB).filter(StaffDB.username == current_user.username).first()
    if not db_staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    return Staff(
        id=str(db_staff.id),
        fullName=db_staff.fullName,
        username=db_staff.username,
        role=StaffRole(db_staff.role),
        isActive=db_staff.isActive,
        createdAt=db_staff.createdAt.isoformat()
    )

@router.patch("/{staff_id}", response_model=Staff)
async def update_staff(
    staff_id: str,
    staff_update: StaffUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update staff member information."""
    # Check if current user is admin or updating their own profile
    if current_user.role != StaffRole.ADMIN and current_user.user_id != staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    
    db_staff = db.query(StaffDB).filter(StaffDB.id == int(staff_id)).first()
    if not db_staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    # Update only provided fields
    update_data = staff_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password" and value:
            setattr(db_staff, field, get_password_hash(value))
        elif field == "role":
            setattr(db_staff, field, value.value)
        else:
            setattr(db_staff, field, value)
    
    db.commit()
    db.refresh(db_staff)
    
    return Staff(
        id=str(db_staff.id),
        fullName=db_staff.fullName,
        username=db_staff.username,
        role=StaffRole(db_staff.role),
        isActive=db_staff.isActive,
        createdAt=db_staff.createdAt.isoformat()
    )

@router.patch("/{staff_id}/toggle-status", response_model=MessageResponse)
async def toggle_staff_status(
    staff_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Toggle staff member active status."""
    # Check if current user is admin
    if current_user.role != StaffRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can toggle staff status"
        )
    
    db_staff = db.query(StaffDB).filter(StaffDB.id == int(staff_id)).first()
    if not db_staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    # Prevent admin from deactivating themselves
    if current_user.user_id == staff_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    db_staff.isActive = not db_staff.isActive
    db.commit()
    
    status_text = "activated" if db_staff.isActive else "deactivated"
    return MessageResponse(message=f"Staff member {status_text} successfully")

@router.delete("/{staff_id}", response_model=MessageResponse)
async def delete_staff(
    staff_id: str, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a staff member."""
    # Check if current user is admin
    if current_user.role != StaffRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete staff members"
        )
    
    db_staff = db.query(StaffDB).filter(StaffDB.id == int(staff_id)).first()
    if not db_staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    # Prevent admin from deleting themselves
    if current_user.user_id == staff_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    db.delete(db_staff)
    db.commit()
    return MessageResponse(message="Staff member deleted successfully")

@router.get("/{staff_id}", response_model=Staff)
async def get_staff_by_id(
    staff_id: str, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get staff member by ID."""
    # Check if current user is admin or viewing their own profile
    if current_user.role != StaffRole.ADMIN and current_user.user_id != staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )
    
    db_staff = db.query(StaffDB).filter(StaffDB.id == int(staff_id)).first()
    if not db_staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    return Staff(
        id=str(db_staff.id),
        fullName=db_staff.fullName,
        username=db_staff.username,
        role=StaffRole(db_staff.role),
        isActive=db_staff.isActive,
        createdAt=db_staff.createdAt.isoformat()
    )
