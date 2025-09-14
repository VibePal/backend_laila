from fastapi import APIRouter, HTTPException, status, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from ..models import Token, LoginRequest, SignupRequest, Staff, StaffCreate, MessageResponse, StaffRole
from ..auth import (
    get_current_user, 
    get_password_hash, 
    create_access_token, 
    verify_password
)
from datetime import datetime, timedelta
from typing import Optional
import uuid

# Import database dependencies
from sqlalchemy.orm import Session
from ..database import get_db
from ..models_sqlalchemy import Staff as StaffDB

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={401: {"description": "Unauthorized"}},
)


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login staff member and return access token."""
    # Find staff by username
    staff = db.query(StaffDB).filter(StaffDB.username == login_data.username).first()
    
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(login_data.password, staff.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if staff is active
    if not staff.isActive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": staff.username, "user_id": str(staff.id), "role": staff.role},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 30 * 60  # 30 minutes in seconds
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: dict = Depends(get_current_user)):
    """Refresh access token."""
    # Create new access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": current_user.username, "user_id": current_user.user_id, "role": current_user.role},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 30 * 60  # 30 minutes in seconds
    }

@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout staff member (in production, you might want to blacklist the token)."""
    return MessageResponse(message="Successfully logged out")

@router.get("/me", response_model=Staff)
async def get_current_staff_info(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current staff member information."""
    # Find staff by username
    staff = db.query(StaffDB).filter(StaffDB.username == current_user.username).first()
    
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    return Staff(
        id=str(staff.id),
        fullName=staff.fullName,
        username=staff.username,
        role=StaffRole(staff.role),
        isActive=staff.isActive,
        createdAt=staff.createdAt.isoformat()
    )

@router.post("/signup", response_model=Staff, status_code=status.HTTP_201_CREATED)
async def signup(signup_data: SignupRequest, db: Session = Depends(get_db)):
    """Signup new admin account with username and password."""
    # Check if username already exists
    existing_user = db.query(StaffDB).filter(StaffDB.username == signup_data.username).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create new admin account
    admin = StaffDB(
        fullName=signup_data.username.title(),  # Use username as full name, capitalized
        username=signup_data.username,
        password=get_password_hash(signup_data.password),
        role="admin",  # All signup accounts are admins
        isActive=True
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    return Staff(
        id=str(admin.id),
        fullName=admin.fullName,
        username=admin.username,
        role=StaffRole(admin.role),
        isActive=admin.isActive,
        createdAt=admin.createdAt.isoformat()
    )

@router.post("/setup-admin", response_model=Staff, status_code=status.HTTP_201_CREATED)
async def setup_admin(db: Session = Depends(get_db)):
    """Setup initial admin account (first time setup only)."""
    # Check if any admin exists
    admin_exists = db.query(StaffDB).filter(StaffDB.role == "admin").first()
    
    if admin_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin account already exists"
        )
    
    # Create default admin account
    admin = StaffDB(
        fullName="System Administrator",
        username="admin",
        password=get_password_hash("admin123"),  # Change this in production
        role="admin",
        isActive=True
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    return Staff(
        id=str(admin.id),
        fullName=admin.fullName,
        username=admin.username,
        role=StaffRole(admin.role),
        isActive=admin.isActive,
        createdAt=admin.createdAt.isoformat()
    )
