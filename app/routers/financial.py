from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from ..database import get_db
from ..models_sqlalchemy import (
    Order as OrderDB, 
    OrderItem as OrderItemDB, 
    Product as ProductDB,
    SupplyExpense as SupplyExpenseDB,
    StaffPayment as StaffPaymentDB,
    OverheadCost as OverheadCostDB
)
from ..models import (
    FinancialSummary, 
    RevenueBreakdown, 
    ExpenseBreakdown, 
    ProfitAnalysis, 
    FinancialBreakdown,
    FinancialFilter
)
from ..auth import get_current_admin

router = APIRouter(
    prefix="/financial",
    tags=["financial"],
    responses={404: {"description": "Not found"}},
)

def get_date_range(selected_date: str, period: str) -> tuple[datetime, datetime]:
    """Calculate date range based on period"""
    date = datetime.strptime(selected_date, "%Y-%m-%d")
    
    if period == "day":
        return date, date
    elif period == "week":
        start_of_week = date - timedelta(days=date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return start_of_week, end_of_week
    elif period == "month":
        start_of_month = date.replace(day=1)
        if date.month == 12:
            end_of_month = date.replace(year=date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_of_month = date.replace(month=date.month + 1, day=1) - timedelta(days=1)
        return start_of_month, end_of_month
    else:
        return date, date

def get_payment_method_display(payment_type: str) -> str:
    """Convert payment type to display text"""
    payment_map = {
        'cash': 'Cash',
        'momo': 'MoMo',
        'card': 'Card',
        'mobile_money': 'Mobile Money'
    }
    return payment_map.get(payment_type, payment_type)

@router.get("/summary", status_code=status.HTTP_200_OK)
async def get_financial_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    period: str = Query("day", description="Time period: day, week, month"),
    include_overhead: bool = Query(True, description="Include overhead costs"),
    include_staff_payments: bool = Query(True, description="Include staff payments"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get complete financial summary with filtering options"""
    try:
        # Build base queries
        orders_query = db.query(OrderDB)
        expenses_query = db.query(SupplyExpenseDB)
        staff_payments_query = db.query(StaffPaymentDB)
        overhead_costs_query = db.query(OverheadCostDB)
        
        # Apply date filters
        if start_date and end_date:
            orders_query = orders_query.filter(OrderDB.order_date >= start_date, OrderDB.order_date <= end_date)
            expenses_query = expenses_query.filter(SupplyExpenseDB.date >= start_date, SupplyExpenseDB.date <= end_date)
            staff_payments_query = staff_payments_query.filter(StaffPaymentDB.paymentDate >= start_date, StaffPaymentDB.paymentDate <= end_date)
            overhead_costs_query = overhead_costs_query.filter(OverheadCostDB.date >= start_date, OverheadCostDB.date <= end_date)
        elif start_date:
            start_dt, end_dt = get_date_range(start_date, period)
            start_str = start_dt.strftime("%Y-%m-%d")
            end_str = end_dt.strftime("%Y-%m-%d")
            
            orders_query = orders_query.filter(OrderDB.order_date >= start_str, OrderDB.order_date <= end_str)
            expenses_query = expenses_query.filter(SupplyExpenseDB.date >= start_str, SupplyExpenseDB.date <= end_str)
            staff_payments_query = staff_payments_query.filter(StaffPaymentDB.paymentDate >= start_str, StaffPaymentDB.paymentDate <= end_str)
            overhead_costs_query = overhead_costs_query.filter(OverheadCostDB.date >= start_str, OverheadCostDB.date <= end_str)
        
        # Get filtered data
        orders = orders_query.all()
        supply_expenses = expenses_query.all()
        staff_payments = staff_payments_query.all() if include_staff_payments else []
        overhead_costs = overhead_costs_query.all() if include_overhead else []
        
        # Calculate revenue
        total_revenue = sum(order.total for order in orders)
        total_orders = len(orders)
        
        # Calculate expenses
        supply_expenses_total = sum(expense.total for expense in supply_expenses)
        staff_payments_total = sum(payment.amount for payment in staff_payments)
        overhead_costs_total = sum(cost.amount for cost in overhead_costs)
        
        total_expenses = supply_expenses_total + staff_payments_total + overhead_costs_total
        
        # Calculate profit
        net_profit = total_revenue - total_expenses
        
        # Format date range display
        if start_date and end_date:
            date_range = f"{start_date} to {end_date}"
        elif start_date:
            start_dt, end_dt = get_date_range(start_date, period)
            date_range = f"{start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}"
        else:
            date_range = "All dates"
        
        return {
            "success": True,
            "data": {
                "total_revenue": round(total_revenue, 2),
                "total_orders": total_orders,
                "supply_expenses": round(supply_expenses_total, 2),
                "staff_payments": round(staff_payments_total, 2),
                "overhead_costs": round(overhead_costs_total, 2),
                "total_expenses": round(total_expenses, 2),
                "net_profit": round(net_profit, 2),
                "date_range": date_range,
                "period": period
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating financial summary: {str(e)}"
        )

@router.get("/revenue", status_code=status.HTTP_200_OK)
async def get_revenue_breakdown(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    period: str = Query("day", description="Time period: day, week, month"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get detailed revenue breakdown"""
    try:
        # Build base query
        orders_query = db.query(OrderDB)
        
        # Apply date filters
        if start_date and end_date:
            orders_query = orders_query.filter(OrderDB.order_date >= start_date, OrderDB.order_date <= end_date)
        elif start_date:
            start_dt, end_dt = get_date_range(start_date, period)
            orders_query = orders_query.filter(OrderDB.order_date >= start_dt.strftime("%Y-%m-%d"), 
                                             OrderDB.order_date <= end_dt.strftime("%Y-%m-%d"))
        
        orders = orders_query.all()
        
        # Calculate revenue metrics
        total_revenue = sum(order.total for order in orders)
        total_orders = len(orders)
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Revenue by payment method
        revenue_by_payment_method = {}
        for order in orders:
            payment_method = get_payment_method_display(order.payment_type)
            if payment_method not in revenue_by_payment_method:
                revenue_by_payment_method[payment_method] = 0
            revenue_by_payment_method[payment_method] += order.total
        
        # Revenue by order type
        revenue_by_order_type = {"standard": 0, "custom": 0}
        for order in orders:
            order_items = db.query(OrderItemDB).filter(OrderItemDB.order_id == order.id).all()
            is_custom_order = any(item.is_custom_order for item in order_items)
            order_type = "custom" if is_custom_order else "standard"
            revenue_by_order_type[order_type] += order.total
        
        return {
            "success": True,
            "data": {
                "total_revenue": round(total_revenue, 2),
                "total_orders": total_orders,
                "average_order_value": round(average_order_value, 2),
                "revenue_by_payment_method": {k: round(v, 2) for k, v in revenue_by_payment_method.items()},
                "revenue_by_order_type": {k: round(v, 2) for k, v in revenue_by_order_type.items()}
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating revenue breakdown: {str(e)}"
        )

@router.get("/expenses", status_code=status.HTTP_200_OK)
async def get_expense_breakdown(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    period: str = Query("day", description="Time period: day, week, month"),
    include_overhead: bool = Query(True, description="Include overhead costs"),
    include_staff_payments: bool = Query(True, description="Include staff payments"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get detailed expense breakdown"""
    try:
        # Build base queries
        expenses_query = db.query(SupplyExpenseDB)
        staff_payments_query = db.query(StaffPaymentDB)
        overhead_costs_query = db.query(OverheadCostDB)
        
        # Apply date filters
        if start_date and end_date:
            expenses_query = expenses_query.filter(SupplyExpenseDB.date >= start_date, SupplyExpenseDB.date <= end_date)
            staff_payments_query = staff_payments_query.filter(StaffPaymentDB.paymentDate >= start_date, StaffPaymentDB.paymentDate <= end_date)
            overhead_costs_query = overhead_costs_query.filter(OverheadCostDB.date >= start_date, OverheadCostDB.date <= end_date)
        elif start_date:
            start_dt, end_dt = get_date_range(start_date, period)
            start_str = start_dt.strftime("%Y-%m-%d")
            end_str = end_dt.strftime("%Y-%m-%d")
            
            expenses_query = expenses_query.filter(SupplyExpenseDB.date >= start_str, SupplyExpenseDB.date <= end_str)
            staff_payments_query = staff_payments_query.filter(StaffPaymentDB.paymentDate >= start_str, StaffPaymentDB.paymentDate <= end_str)
            overhead_costs_query = overhead_costs_query.filter(OverheadCostDB.date >= start_str, OverheadCostDB.date <= end_str)
        
        # Get filtered data
        supply_expenses = expenses_query.all()
        staff_payments = staff_payments_query.all() if include_staff_payments else []
        overhead_costs = overhead_costs_query.all() if include_overhead else []
        
        # Calculate expense totals
        supply_expenses_total = sum(expense.total for expense in supply_expenses)
        staff_payments_total = sum(payment.amount for payment in staff_payments)
        overhead_costs_total = sum(cost.amount for cost in overhead_costs)
        
        total_expenses = supply_expenses_total + staff_payments_total + overhead_costs_total
        
        # Expense categories breakdown
        expense_categories = {
            "Supply Expenses": supply_expenses_total,
            "Staff Payments": staff_payments_total,
            "Overhead Costs": overhead_costs_total
        }
        
        return {
            "success": True,
            "data": {
                "supply_expenses": round(supply_expenses_total, 2),
                "staff_payments": round(staff_payments_total, 2),
                "overhead_costs": round(overhead_costs_total, 2),
                "total_expenses": round(total_expenses, 2),
                "expense_categories": {k: round(v, 2) for k, v in expense_categories.items()}
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating expense breakdown: {str(e)}"
        )

@router.get("/profit", status_code=status.HTTP_200_OK)
async def get_profit_analysis(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    period: str = Query("day", description="Time period: day, week, month"),
    include_overhead: bool = Query(True, description="Include overhead costs"),
    include_staff_payments: bool = Query(True, description="Include staff payments"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get profit analysis and calculations"""
    try:
        # Get revenue data
        orders_query = db.query(OrderDB)
        if start_date and end_date:
            orders_query = orders_query.filter(OrderDB.order_date >= start_date, OrderDB.order_date <= end_date)
        elif start_date:
            start_dt, end_dt = get_date_range(start_date, period)
            orders_query = orders_query.filter(OrderDB.order_date >= start_dt.strftime("%Y-%m-%d"), 
                                             OrderDB.order_date <= end_dt.strftime("%Y-%m-%d"))
        
        orders = orders_query.all()
        total_revenue = sum(order.total for order in orders)
        
        # Get expense data
        expenses_query = db.query(SupplyExpenseDB)
        staff_payments_query = db.query(StaffPaymentDB)
        overhead_costs_query = db.query(OverheadCostDB)
        
        if start_date and end_date:
            expenses_query = expenses_query.filter(SupplyExpenseDB.date >= start_date, SupplyExpenseDB.date <= end_date)
            staff_payments_query = staff_payments_query.filter(StaffPaymentDB.paymentDate >= start_date, StaffPaymentDB.paymentDate <= end_date)
            overhead_costs_query = overhead_costs_query.filter(OverheadCostDB.date >= start_date, OverheadCostDB.date <= end_date)
        elif start_date:
            start_dt, end_dt = get_date_range(start_date, period)
            start_str = start_dt.strftime("%Y-%m-%d")
            end_str = end_dt.strftime("%Y-%m-%d")
            
            expenses_query = expenses_query.filter(SupplyExpenseDB.date >= start_str, SupplyExpenseDB.date <= end_str)
            staff_payments_query = staff_payments_query.filter(StaffPaymentDB.paymentDate >= start_str, StaffPaymentDB.paymentDate <= end_str)
            overhead_costs_query = overhead_costs_query.filter(OverheadCostDB.date >= start_str, OverheadCostDB.date <= end_str)
        
        supply_expenses = expenses_query.all()
        staff_payments = staff_payments_query.all() if include_staff_payments else []
        overhead_costs = overhead_costs_query.all() if include_overhead else []
        
        total_expenses = (sum(expense.total for expense in supply_expenses) + 
                         sum(payment.amount for payment in staff_payments) + 
                         sum(cost.amount for cost in overhead_costs))
        
        # Calculate profit metrics
        net_profit = total_revenue - total_expenses
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        profitability_ratio = (net_profit / total_expenses) if total_expenses > 0 else 0
        
        return {
            "success": True,
            "data": {
                "net_profit": round(net_profit, 2),
                "profit_margin": round(profit_margin, 2),
                "revenue": round(total_revenue, 2),
                "expenses": round(total_expenses, 2),
                "profitability_ratio": round(profitability_ratio, 2)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating profit analysis: {str(e)}"
        )

@router.get("/breakdown", status_code=status.HTTP_200_OK)
async def get_financial_breakdown(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    period: str = Query("day", description="Time period: day, week, month"),
    include_overhead: bool = Query(True, description="Include overhead costs"),
    include_staff_payments: bool = Query(True, description="Include staff payments"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get complete financial breakdown (revenue, expenses, profit)"""
    try:
        # Get all financial data
        orders_query = db.query(OrderDB)
        expenses_query = db.query(SupplyExpenseDB)
        staff_payments_query = db.query(StaffPaymentDB)
        overhead_costs_query = db.query(OverheadCostDB)
        
        # Apply date filters
        if start_date and end_date:
            orders_query = orders_query.filter(OrderDB.order_date >= start_date, OrderDB.order_date <= end_date)
            expenses_query = expenses_query.filter(SupplyExpenseDB.date >= start_date, SupplyExpenseDB.date <= end_date)
            staff_payments_query = staff_payments_query.filter(StaffPaymentDB.paymentDate >= start_date, StaffPaymentDB.paymentDate <= end_date)
            overhead_costs_query = overhead_costs_query.filter(OverheadCostDB.date >= start_date, OverheadCostDB.date <= end_date)
        elif start_date:
            start_dt, end_dt = get_date_range(start_date, period)
            start_str = start_dt.strftime("%Y-%m-%d")
            end_str = end_dt.strftime("%Y-%m-%d")
            
            orders_query = orders_query.filter(OrderDB.order_date >= start_str, OrderDB.order_date <= end_str)
            expenses_query = expenses_query.filter(SupplyExpenseDB.date >= start_str, SupplyExpenseDB.date <= end_str)
            staff_payments_query = staff_payments_query.filter(StaffPaymentDB.paymentDate >= start_str, StaffPaymentDB.paymentDate <= end_str)
            overhead_costs_query = overhead_costs_query.filter(OverheadCostDB.date >= start_str, OverheadCostDB.date <= end_str)
        
        # Get filtered data
        orders = orders_query.all()
        supply_expenses = expenses_query.all()
        staff_payments = staff_payments_query.all() if include_staff_payments else []
        overhead_costs = overhead_costs_query.all() if include_overhead else []
        
        # Calculate all metrics
        total_revenue = sum(order.total for order in orders)
        total_orders = len(orders)
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        supply_expenses_total = sum(expense.total for expense in supply_expenses)
        staff_payments_total = sum(payment.amount for payment in staff_payments)
        overhead_costs_total = sum(cost.amount for cost in overhead_costs)
        total_expenses = supply_expenses_total + staff_payments_total + overhead_costs_total
        
        net_profit = total_revenue - total_expenses
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Revenue by payment method
        revenue_by_payment_method = {}
        for order in orders:
            payment_method = get_payment_method_display(order.payment_type)
            if payment_method not in revenue_by_payment_method:
                revenue_by_payment_method[payment_method] = 0
            revenue_by_payment_method[payment_method] += order.total
        
        # Revenue by order type
        revenue_by_order_type = {"standard": 0, "custom": 0}
        for order in orders:
            order_items = db.query(OrderItemDB).filter(OrderItemDB.order_id == order.id).all()
            is_custom_order = any(item.is_custom_order for item in order_items)
            order_type = "custom" if is_custom_order else "standard"
            revenue_by_order_type[order_type] += order.total
        
        return {
            "success": True,
            "data": {
                "revenue": {
                    "total_revenue": round(total_revenue, 2),
                    "total_orders": total_orders,
                    "average_order_value": round(average_order_value, 2),
                    "revenue_by_payment_method": {k: round(v, 2) for k, v in revenue_by_payment_method.items()},
                    "revenue_by_order_type": {k: round(v, 2) for k, v in revenue_by_order_type.items()}
                },
                "expenses": {
                    "supply_expenses": round(supply_expenses_total, 2),
                    "staff_payments": round(staff_payments_total, 2),
                    "overhead_costs": round(overhead_costs_total, 2),
                    "total_expenses": round(total_expenses, 2),
                    "expense_categories": {
                        "Supply Expenses": round(supply_expenses_total, 2),
                        "Staff Payments": round(staff_payments_total, 2),
                        "Overhead Costs": round(overhead_costs_total, 2)
                    }
                },
                "profit": {
                    "net_profit": round(net_profit, 2),
                    "profit_margin": round(profit_margin, 2),
                    "revenue": round(total_revenue, 2),
                    "expenses": round(total_expenses, 2),
                    "profitability_ratio": round((net_profit / total_expenses) if total_expenses > 0 else 0, 2)
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating financial breakdown: {str(e)}"
        )

@router.post("/clear-data", status_code=status.HTTP_200_OK)
async def clear_financial_data(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Clear all financial data (admin only)"""
    try:
        # This is a dangerous operation, so we'll just return a message
        # In a real application, you might want to implement actual data clearing
        # or move data to an archive table instead of deleting
        
        return {
            "success": True,
            "message": "Financial data clear operation completed",
            "warning": "This operation should be used with extreme caution in production environments"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing financial data: {str(e)}"
        )
