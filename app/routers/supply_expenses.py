from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from ..models import SupplyExpense, SupplyExpenseCreate, SupplyExpenseUpdate, ExpenseCategory
from ..models_sqlalchemy import SupplyExpense as SupplyExpenseDB
from ..database import get_db
from ..auth import get_current_admin

router = APIRouter(prefix="/supply-expenses", tags=["supply-expenses"])

@router.post("/", response_model=SupplyExpense, summary="Create Supply Expense")
async def create_supply_expense(
    expense: SupplyExpenseCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new supply expense"""
    # Parse date string to datetime
    expense_date = datetime.fromisoformat(expense.date.replace('Z', '+00:00'))
    
    # Calculate total and price per unit
    total = expense.quantity * expense.costPerItem
    price_per_unit = None
    if expense.packageSize and expense.packageSize > 0:
        price_per_unit = expense.costPerItem / expense.packageSize
    
    # Create database model instance
    db_expense = SupplyExpenseDB(
        date=expense_date,
        supplier=expense.supplier,
        items=expense.items,
        quantity=expense.quantity,
        costPerItem=expense.costPerItem,
        category=expense.category.value,
        purchaseUnit=expense.purchaseUnit,
        packageSize=expense.packageSize,
        total=total,
        pricePerUnit=price_per_unit
    )
    
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    
    # Convert to Pydantic model for response
    return SupplyExpense(
        id=str(db_expense.id),
        date=expense.date,
        supplier=db_expense.supplier,
        items=db_expense.items,
        quantity=db_expense.quantity,
        costPerItem=db_expense.costPerItem,
        category=ExpenseCategory(db_expense.category),
        purchaseUnit=db_expense.purchaseUnit,
        packageSize=db_expense.packageSize,
        total=db_expense.total,
        pricePerUnit=db_expense.pricePerUnit,
        createdAt=db_expense.createdAt.isoformat()
    )

@router.get("/", response_model=List[SupplyExpense], summary="Get All Supply Expenses")
async def get_supply_expenses(
    date: Optional[str] = Query(None, description="Filter by specific date (YYYY-MM-DD)"),
    category: Optional[ExpenseCategory] = Query(None, description="Filter by expense category"),
    supplier: Optional[str] = Query(None, description="Filter by supplier name"),
    db: Session = Depends(get_db)
):
    """Get all supply expenses with optional filtering"""
    query = db.query(SupplyExpenseDB)
    
    # Apply filters
    if date:
        filter_date = datetime.fromisoformat(date)
        query = query.filter(SupplyExpenseDB.date == filter_date)
    if category:
        query = query.filter(SupplyExpenseDB.category == category.value)
    if supplier:
        query = query.filter(SupplyExpenseDB.supplier.ilike(f"%{supplier}%"))
    
    db_expenses = query.all()
    
    # Convert to Pydantic models
    expenses = []
    for db_expense in db_expenses:
        expenses.append(SupplyExpense(
            id=str(db_expense.id),
            date=db_expense.date.isoformat(),
            supplier=db_expense.supplier,
            items=db_expense.items,
            quantity=db_expense.quantity,
            costPerItem=db_expense.costPerItem,
            category=ExpenseCategory(db_expense.category),
            purchaseUnit=db_expense.purchaseUnit,
            packageSize=db_expense.packageSize,
            total=db_expense.total,
            pricePerUnit=db_expense.pricePerUnit,
            createdAt=db_expense.createdAt.isoformat()
        ))
    
    return expenses

@router.get("/{expense_id}", response_model=SupplyExpense, summary="Get Supply Expense by ID")
async def get_supply_expense(expense_id: str, db: Session = Depends(get_db)):
    """Get a specific supply expense by ID"""
    db_expense = db.query(SupplyExpenseDB).filter(SupplyExpenseDB.id == int(expense_id)).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Supply expense not found")
    
    return SupplyExpense(
        id=str(db_expense.id),
        date=db_expense.date.isoformat(),
        supplier=db_expense.supplier,
        items=db_expense.items,
        quantity=db_expense.quantity,
        costPerItem=db_expense.costPerItem,
        category=ExpenseCategory(db_expense.category),
        purchaseUnit=db_expense.purchaseUnit,
        packageSize=db_expense.packageSize,
        total=db_expense.total,
        pricePerUnit=db_expense.pricePerUnit,
        createdAt=db_expense.createdAt.isoformat()
    )

@router.get("/by-date/{date}", response_model=List[SupplyExpense], summary="Get Supply Expenses by Date")
async def get_supply_expenses_by_date(date: str, db: Session = Depends(get_db)):
    """Get all supply expenses for a specific date"""
    filter_date = datetime.fromisoformat(date)
    db_expenses = db.query(SupplyExpenseDB).filter(SupplyExpenseDB.date == filter_date).all()
    
    expenses = []
    for db_expense in db_expenses:
        expenses.append(SupplyExpense(
            id=str(db_expense.id),
            date=db_expense.date.isoformat(),
            supplier=db_expense.supplier,
            items=db_expense.items,
            quantity=db_expense.quantity,
            costPerItem=db_expense.costPerItem,
            category=ExpenseCategory(db_expense.category),
            purchaseUnit=db_expense.purchaseUnit,
            packageSize=db_expense.packageSize,
            total=db_expense.total,
            pricePerUnit=db_expense.pricePerUnit,
            createdAt=db_expense.createdAt.isoformat()
        ))
    
    return expenses

@router.get("/by-supplier/{supplier_name}", response_model=List[SupplyExpense], summary="Get Supply Expenses by Supplier")
async def get_supply_expenses_by_supplier(supplier_name: str, db: Session = Depends(get_db)):
    """Get all supply expenses for a specific supplier"""
    db_expenses = db.query(SupplyExpenseDB).filter(SupplyExpenseDB.supplier.ilike(f"%{supplier_name}%")).all()
    
    expenses = []
    for db_expense in db_expenses:
        expenses.append(SupplyExpense(
            id=str(db_expense.id),
            date=db_expense.date.isoformat(),
            supplier=db_expense.supplier,
            items=db_expense.items,
            quantity=db_expense.quantity,
            costPerItem=db_expense.costPerItem,
            category=ExpenseCategory(db_expense.category),
            purchaseUnit=db_expense.purchaseUnit,
            packageSize=db_expense.packageSize,
            total=db_expense.total,
            pricePerUnit=db_expense.pricePerUnit,
            createdAt=db_expense.createdAt.isoformat()
        ))
    
    return expenses

@router.patch("/{expense_id}", response_model=SupplyExpense, summary="Update Supply Expense")
async def update_supply_expense(
    expense_id: str,
    expense_update: SupplyExpenseUpdate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Update a supply expense"""
    db_expense = db.query(SupplyExpenseDB).filter(SupplyExpenseDB.id == int(expense_id)).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Supply expense not found")
    
    update_data = expense_update.dict(exclude_unset=True)
    
    # Update fields
    for field, value in update_data.items():
        if field == "date":
            setattr(db_expense, field, datetime.fromisoformat(value.replace('Z', '+00:00')))
        elif field == "category":
            setattr(db_expense, field, value.value)
        else:
            setattr(db_expense, field, value)
    
    # Recalculate total and price per unit if relevant fields are updated
    if "quantity" in update_data or "costPerItem" in update_data:
        db_expense.total = db_expense.quantity * db_expense.costPerItem
    
    if "costPerItem" in update_data or "packageSize" in update_data:
        if db_expense.packageSize and db_expense.packageSize > 0:
            db_expense.pricePerUnit = db_expense.costPerItem / db_expense.packageSize
        else:
            db_expense.pricePerUnit = None
    
    db.commit()
    db.refresh(db_expense)
    
    return SupplyExpense(
        id=str(db_expense.id),
        date=db_expense.date.isoformat(),
        supplier=db_expense.supplier,
        items=db_expense.items,
        quantity=db_expense.quantity,
        costPerItem=db_expense.costPerItem,
        category=ExpenseCategory(db_expense.category),
        purchaseUnit=db_expense.purchaseUnit,
        packageSize=db_expense.packageSize,
        total=db_expense.total,
        pricePerUnit=db_expense.pricePerUnit,
        createdAt=db_expense.createdAt.isoformat()
    )

@router.delete("/{expense_id}", summary="Delete Supply Expense")
async def delete_supply_expense(
    expense_id: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Delete a supply expense"""
    db_expense = db.query(SupplyExpenseDB).filter(SupplyExpenseDB.id == int(expense_id)).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Supply expense not found")
    
    db.delete(db_expense)
    db.commit()
    return {"message": "Supply expense deleted successfully"}

@router.get("/summary/total", summary="Get Supply Expenses Summary")
async def get_supply_expenses_summary(
    date: Optional[str] = Query(None, description="Filter by specific date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get summary statistics for supply expenses"""
    from sqlalchemy import func
    
    query = db.query(SupplyExpenseDB)
    
    if date:
        filter_date = datetime.fromisoformat(date)
        query = query.filter(SupplyExpenseDB.date == filter_date)
    
    # Get aggregated data
    result = query.with_entities(
        func.count(SupplyExpenseDB.id).label('expense_count'),
        func.sum(SupplyExpenseDB.total).label('total_amount'),
        func.avg(SupplyExpenseDB.costPerItem).label('avg_cost_per_item')
    ).first()
    
    expense_count = result.expense_count or 0
    total_amount = result.total_amount or 0.0
    avg_cost_per_item = result.avg_cost_per_item or 0.0
    
    return {
        "totalExpenses": expense_count,
        "totalAmount": round(total_amount, 2),
        "averageCostPerItem": round(avg_cost_per_item, 2),
        "expenseCount": expense_count
    }
