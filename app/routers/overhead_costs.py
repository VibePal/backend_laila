from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from typing import List, Optional

from ..database import get_db
from ..models_sqlalchemy import OverheadCost as OverheadCostDB
from ..models import OverheadCostCreate, OverheadCostUpdate, OverheadCost
from ..auth import get_current_admin

router = APIRouter(
    prefix="/overhead-costs",
    tags=["overhead-costs"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_overhead_cost(
    overhead_cost_data: OverheadCostCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new overhead cost"""
    try:
        # Generate unique ID
        overhead_cost_id = f"OHC-{int(datetime.now().timestamp() * 1000)}"
        
        # Create overhead cost record
        db_overhead_cost = OverheadCostDB(
            id=overhead_cost_id,
            category=overhead_cost_data.category,
            description=overhead_cost_data.description,
            amount=overhead_cost_data.amount,
            date=overhead_cost_data.date,
            recurring=overhead_cost_data.recurring,
            frequency=overhead_cost_data.frequency,
            cost_type=overhead_cost_data.cost_type
        )
        
        db.add(db_overhead_cost)
        db.commit()
        db.refresh(db_overhead_cost)
        
        return {
            "success": True,
            "message": "Overhead cost created successfully",
            "overhead_cost_id": overhead_cost_id,
            "data": {
                "id": db_overhead_cost.id,
                "category": db_overhead_cost.category,
                "description": db_overhead_cost.description,
                "amount": db_overhead_cost.amount,
                "date": db_overhead_cost.date,
                "recurring": db_overhead_cost.recurring,
                "frequency": db_overhead_cost.frequency,
                "cost_type": db_overhead_cost.cost_type,
                "created_at": db_overhead_cost.created_at.isoformat(),
                "updated_at": db_overhead_cost.updated_at.isoformat()
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating overhead cost: {str(e)}"
        )

@router.get("/", status_code=status.HTTP_200_OK)
async def get_overhead_costs(
    skip: int = 0,
    limit: int = 100,
    cost_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get all overhead costs with optional filtering"""
    try:
        # Build query
        query = db.query(OverheadCostDB)
        
        # Apply cost type filter if provided
        if cost_type:
            query = query.filter(OverheadCostDB.cost_type == cost_type)
        
        # Apply pagination
        overhead_costs = query.offset(skip).limit(limit).all()
        
        # Convert to response format
        result = []
        for cost in overhead_costs:
            result.append({
                "id": cost.id,
                "category": cost.category,
                "description": cost.description,
                "amount": cost.amount,
                "date": cost.date,
                "recurring": cost.recurring,
                "frequency": cost.frequency,
                "cost_type": cost.cost_type,
                "created_at": cost.created_at.isoformat(),
                "updated_at": cost.updated_at.isoformat()
            })
        
        return {
            "success": True,
            "data": result,
            "total_count": len(result)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching overhead costs: {str(e)}"
        )

@router.get("/{overhead_cost_id}", status_code=status.HTTP_200_OK)
async def get_overhead_cost(
    overhead_cost_id: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get a specific overhead cost by ID"""
    try:
        overhead_cost = db.query(OverheadCostDB).filter(OverheadCostDB.id == overhead_cost_id).first()
        
        if not overhead_cost:
            raise HTTPException(
                status_code=404,
                detail="Overhead cost not found"
            )
        
        return {
            "success": True,
            "data": {
                "id": overhead_cost.id,
                "category": overhead_cost.category,
                "description": overhead_cost.description,
                "amount": overhead_cost.amount,
                "date": overhead_cost.date,
                "recurring": overhead_cost.recurring,
                "frequency": overhead_cost.frequency,
                "cost_type": overhead_cost.cost_type,
                "created_at": overhead_cost.created_at.isoformat(),
                "updated_at": overhead_cost.updated_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching overhead cost: {str(e)}"
        )

@router.put("/{overhead_cost_id}", status_code=status.HTTP_200_OK)
async def update_overhead_cost(
    overhead_cost_id: str,
    overhead_cost_data: OverheadCostUpdate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Update an existing overhead cost"""
    try:
        # Find the overhead cost
        overhead_cost = db.query(OverheadCostDB).filter(OverheadCostDB.id == overhead_cost_id).first()
        
        if not overhead_cost:
            raise HTTPException(
                status_code=404,
                detail="Overhead cost not found"
            )
        
        # Update fields if provided
        update_data = overhead_cost_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(overhead_cost, field, value)
        
        # Update the updated_at timestamp
        overhead_cost.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(overhead_cost)
        
        return {
            "success": True,
            "message": "Overhead cost updated successfully",
            "data": {
                "id": overhead_cost.id,
                "category": overhead_cost.category,
                "description": overhead_cost.description,
                "amount": overhead_cost.amount,
                "date": overhead_cost.date,
                "recurring": overhead_cost.recurring,
                "frequency": overhead_cost.frequency,
                "cost_type": overhead_cost.cost_type,
                "created_at": overhead_cost.created_at.isoformat(),
                "updated_at": overhead_cost.updated_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating overhead cost: {str(e)}"
        )

@router.delete("/{overhead_cost_id}", status_code=status.HTTP_200_OK)
async def delete_overhead_cost(
    overhead_cost_id: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Delete an overhead cost"""
    try:
        # Find the overhead cost
        overhead_cost = db.query(OverheadCostDB).filter(OverheadCostDB.id == overhead_cost_id).first()
        
        if not overhead_cost:
            raise HTTPException(
                status_code=404,
                detail="Overhead cost not found"
            )
        
        # Delete the overhead cost
        db.delete(overhead_cost)
        db.commit()
        
        return {
            "success": True,
            "message": "Overhead cost deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting overhead cost: {str(e)}"
        )

@router.get("/stats/summary", status_code=status.HTTP_200_OK)
async def get_overhead_cost_summary(
    cost_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get summary statistics for overhead costs"""
    try:
        # Build query
        query = db.query(OverheadCostDB)
        
        # Apply cost type filter if provided
        if cost_type:
            query = query.filter(OverheadCostDB.cost_type == cost_type)
        
        overhead_costs = query.all()
        
        # Calculate statistics
        total_recurring_monthly = 0
        total_one_time = 0
        
        for cost in overhead_costs:
            if cost.recurring:
                if cost.frequency == "Monthly":
                    total_recurring_monthly += cost.amount
                elif cost.frequency == "Quarterly":
                    total_recurring_monthly += cost.amount / 3
                elif cost.frequency == "Annually":
                    total_recurring_monthly += cost.amount / 12
            else:
                total_one_time += cost.amount
        
        return {
            "success": True,
            "data": {
                "total_recurring_monthly": round(total_recurring_monthly, 2),
                "total_one_time": round(total_one_time, 2),
                "total_costs": round(total_recurring_monthly + total_one_time, 2),
                "count": len(overhead_costs)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating overhead cost summary: {str(e)}"
        )
