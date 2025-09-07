from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List
from sqlalchemy.orm import Session
from ..models import StaffPayment, StaffPaymentCreate, StaffPaymentUpdate, MessageResponse, PaginatedResponse
from ..models_sqlalchemy import StaffPayment as StaffPaymentDB, Staff as StaffDB
from ..database import get_db
from ..auth import get_current_user
from datetime import datetime

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=StaffPayment, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment: StaffPaymentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new staff payment."""
    # Check if current user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create payments"
        )
    
    # Validate staff exists and is active
    staff = db.query(StaffDB).filter(StaffDB.id == int(payment.staffId)).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )
    
    if not staff.isActive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create payment for inactive staff member"
        )
    
    # Create payment
    payment_date = datetime.fromisoformat(payment.paymentDate.replace('Z', '+00:00'))
    
    db_payment = StaffPaymentDB(
        staffId=int(payment.staffId),
        amount=payment.amount,
        paymentDate=payment_date
    )
    
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    
    return StaffPayment(
        id=str(db_payment.id),
        staffId=str(db_payment.staffId),
        amount=db_payment.amount,
        paymentDate=payment.paymentDate,
        staffName=staff.fullName,
        createdAt=db_payment.createdAt.isoformat()
    )

@router.get("/", response_model=PaginatedResponse)
async def get_payments(
    skip: int = Query(0, ge=0, description="Number of payments to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of payments to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get paginated list of payments."""
    # Check if current user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view all payments"
        )
    
    # Get total count
    total = db.query(StaffPaymentDB).count()
    
    # Get paginated payments with staff information
    db_payments = db.query(StaffPaymentDB, StaffDB).join(
        StaffDB, StaffPaymentDB.staffId == StaffDB.id
    ).offset(skip).limit(limit).all()
    
    payments = []
    for payment, staff in db_payments:
        payments.append({
            "id": str(payment.id),
            "staffId": str(payment.staffId),
            "amount": payment.amount,
            "paymentDate": payment.paymentDate.isoformat(),
            "staffName": staff.fullName,
            "createdAt": payment.createdAt.isoformat()
        })
    
    # Calculate pagination info
    page = (skip // limit) + 1
    pages = (total + limit - 1) // limit
    
    return PaginatedResponse(
        items=payments,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )

@router.get("/staff/{staff_id}", response_model=List[StaffPayment])
async def get_staff_payments(
    staff_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get payments for a specific staff member."""
    # Check if current user is admin or viewing their own payments
    if current_user.role != "admin" and current_user.user_id != staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own payments"
        )
    
    # Get staff information
    staff = db.query(StaffDB).filter(StaffDB.id == int(staff_id)).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    # Get payments for this staff member
    db_payments = db.query(StaffPaymentDB).filter(StaffPaymentDB.staffId == int(staff_id)).all()
    
    payments = []
    for payment in db_payments:
        payments.append(StaffPayment(
            id=str(payment.id),
            staffId=str(payment.staffId),
            amount=payment.amount,
            paymentDate=payment.paymentDate.isoformat(),
            staffName=staff.fullName,
            createdAt=payment.createdAt.isoformat()
        ))
    
    return payments

@router.get("/{payment_id}", response_model=StaffPayment)
async def get_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get payment by ID."""
    db_payment = db.query(StaffPaymentDB).filter(StaffPaymentDB.id == int(payment_id)).first()
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Check if current user is admin or the payment belongs to them
    if current_user.role != "admin" and current_user.user_id != str(db_payment.staffId):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own payments"
        )
    
    # Get staff information
    staff = db.query(StaffDB).filter(StaffDB.id == db_payment.staffId).first()
    
    return StaffPayment(
        id=str(db_payment.id),
        staffId=str(db_payment.staffId),
        amount=db_payment.amount,
        paymentDate=db_payment.paymentDate.isoformat(),
        staffName=staff.fullName if staff else "Unknown",
        createdAt=db_payment.createdAt.isoformat()
    )

@router.put("/{payment_id}", response_model=StaffPayment)
async def update_payment(
    payment_id: str,
    payment_update: StaffPaymentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a payment."""
    # Check if current user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update payments"
        )
    
    db_payment = db.query(StaffPaymentDB).filter(StaffPaymentDB.id == int(payment_id)).first()
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Update only provided fields
    update_data = payment_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "paymentDate":
            setattr(db_payment, field, datetime.fromisoformat(value.replace('Z', '+00:00')))
        else:
            setattr(db_payment, field, value)
    
    db.commit()
    db.refresh(db_payment)
    
    # Get staff information
    staff = db.query(StaffDB).filter(StaffDB.id == db_payment.staffId).first()
    
    return StaffPayment(
        id=str(db_payment.id),
        staffId=str(db_payment.staffId),
        amount=db_payment.amount,
        paymentDate=db_payment.paymentDate.isoformat(),
        staffName=staff.fullName if staff else "Unknown",
        createdAt=db_payment.createdAt.isoformat()
    )

@router.delete("/{payment_id}", response_model=MessageResponse)
async def delete_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a payment."""
    # Check if current user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete payments"
        )
    
    db_payment = db.query(StaffPaymentDB).filter(StaffPaymentDB.id == int(payment_id)).first()
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    db.delete(db_payment)
    db.commit()
    return MessageResponse(message="Payment deleted successfully")

@router.get("/summary/total", response_model=dict)
async def get_payment_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get payment summary statistics."""
    # Check if current user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view payment summaries"
        )
    
    from sqlalchemy import func
    
    result = db.query(
        func.count(StaffPaymentDB.id).label('total_payments'),
        func.sum(StaffPaymentDB.amount).label('total_amount'),
        func.avg(StaffPaymentDB.amount).label('avg_amount')
    ).first()
    
    total_payments = result.total_payments or 0
    total_amount = result.total_amount or 0.0
    avg_amount = result.avg_amount or 0.0
    
    return {
        "totalPayments": total_payments,
        "totalAmount": round(total_amount, 2),
        "averageAmount": round(avg_amount, 2)
    }
