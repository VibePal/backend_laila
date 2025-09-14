from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import csv
import io
import json

from ..database import get_db
from ..models_sqlalchemy import Order as OrderDB, OrderItem as OrderItemDB, Product as ProductDB
from ..models import SalesSummary, PaymentBreakdown, ProductBreakdown, SalesBreakdown, SalesFilter, SalesExportRequest
from ..auth import get_current_admin

router = APIRouter(
    prefix="/sales",
    tags=["sales"],
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

def get_order_type_display(order_type: str) -> str:
    """Convert order type to display text"""
    return "Custom" if order_type == "custom" else "Standard"

@router.get("/summary", status_code=status.HTTP_200_OK)
async def get_sales_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    period: str = Query("day", description="Time period: day, week, month"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    order_type: Optional[str] = Query(None, description="Filter by order type: standard, custom"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get sales summary with filtering options"""
    try:
        # Build base query
        query = db.query(OrderDB)
        
        # Apply date filters
        if start_date and end_date:
            query = query.filter(OrderDB.order_date >= start_date, OrderDB.order_date <= end_date)
        elif start_date:
            # Calculate date range based on period
            start_dt, end_dt = get_date_range(start_date, period)
            query = query.filter(OrderDB.order_date >= start_dt.strftime("%Y-%m-%d"), 
                               OrderDB.order_date <= end_dt.strftime("%Y-%m-%d"))
        
        # Apply payment method filter
        if payment_method:
            query = query.filter(OrderDB.payment_type == payment_method)
        
        # Apply order type filter (check if any item is custom)
        if order_type:
            if order_type == "custom":
                query = query.join(OrderItemDB).filter(OrderItemDB.is_custom_order == True)
            elif order_type == "standard":
                query = query.join(OrderItemDB).filter(OrderItemDB.is_custom_order == False)
        
        orders = query.all()
        
        # Calculate summary
        total_orders = len(orders)
        total_sales = sum(order.total for order in orders)
        total_revenue = total_sales  # Same as total sales
        
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
                "total_orders": total_orders,
                "total_sales": round(total_sales, 2),
                "total_revenue": round(total_revenue, 2),
                "date_range": date_range,
                "period": period
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating sales summary: {str(e)}"
        )

@router.get("/breakdown/payment", status_code=status.HTTP_200_OK)
async def get_payment_breakdown(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    period: str = Query("day", description="Time period: day, week, month"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get payment method breakdown"""
    try:
        # Build base query
        query = db.query(OrderDB)
        
        # Apply date filters
        if start_date and end_date:
            query = query.filter(OrderDB.order_date >= start_date, OrderDB.order_date <= end_date)
        elif start_date:
            start_dt, end_dt = get_date_range(start_date, period)
            query = query.filter(OrderDB.order_date >= start_dt.strftime("%Y-%m-%d"), 
                               OrderDB.order_date <= end_dt.strftime("%Y-%m-%d"))
        
        orders = query.all()
        
        # Calculate payment breakdown
        payment_breakdown = {}
        total_revenue = sum(order.total for order in orders)
        
        for order in orders:
            payment_method = get_payment_method_display(order.payment_type)
            if payment_method not in payment_breakdown:
                payment_breakdown[payment_method] = {"amount": 0, "count": 0}
            payment_breakdown[payment_method]["amount"] += order.total
            payment_breakdown[payment_method]["count"] += 1
        
        # Convert to response format
        result = []
        for method, data in payment_breakdown.items():
            percentage = (data["amount"] / total_revenue * 100) if total_revenue > 0 else 0
            result.append({
                "payment_method": method,
                "amount": round(data["amount"], 2),
                "percentage": round(percentage, 1),
                "count": data["count"]
            })
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating payment breakdown: {str(e)}"
        )

@router.get("/breakdown/products", status_code=status.HTTP_200_OK)
async def get_product_breakdown(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    period: str = Query("day", description="Time period: day, week, month"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get product category breakdown"""
    try:
        # Build base query
        query = db.query(OrderDB)
        
        # Apply date filters
        if start_date and end_date:
            query = query.filter(OrderDB.order_date >= start_date, OrderDB.order_date <= end_date)
        elif start_date:
            start_dt, end_dt = get_date_range(start_date, period)
            query = query.filter(OrderDB.order_date >= start_dt.strftime("%Y-%m-%d"), 
                               OrderDB.order_date <= end_dt.strftime("%Y-%m-%d"))
        
        orders = query.all()
        
        # Get all products for category lookup
        products = {p.id: p for p in db.query(ProductDB).all()}
        
        # Calculate product breakdown
        product_breakdown = {}
        total_revenue = 0
        
        for order in orders:
            order_items = db.query(OrderItemDB).filter(OrderItemDB.order_id == order.id).all()
            for item in order_items:
                product = products.get(item.product_id)
                category = product.category if product else "Unknown"
                
                if category not in product_breakdown:
                    product_breakdown[category] = {"amount": 0, "count": 0}
                product_breakdown[category]["amount"] += item.subtotal
                product_breakdown[category]["count"] += item.quantity
                total_revenue += item.subtotal
        
        # Convert to response format
        result = []
        for category, data in product_breakdown.items():
            percentage = (data["amount"] / total_revenue * 100) if total_revenue > 0 else 0
            result.append({
                "product_category": category,
                "amount": round(data["amount"], 2),
                "percentage": round(percentage, 1),
                "count": data["count"]
            })
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating product breakdown: {str(e)}"
        )

@router.get("/orders", status_code=status.HTTP_200_OK)
async def get_sales_orders(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    period: str = Query("day", description="Time period: day, week, month"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    order_type: Optional[str] = Query(None, description="Filter by order type: standard, custom"),
    skip: int = Query(0, description="Number of orders to skip"),
    limit: int = Query(100, description="Maximum number of orders to return"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get filtered orders for sales analysis"""
    try:
        # Build base query
        query = db.query(OrderDB)
        
        # Apply date filters
        if start_date and end_date:
            query = query.filter(OrderDB.order_date >= start_date, OrderDB.order_date <= end_date)
        elif start_date:
            start_dt, end_dt = get_date_range(start_date, period)
            query = query.filter(OrderDB.order_date >= start_dt.strftime("%Y-%m-%d"), 
                               OrderDB.order_date <= end_dt.strftime("%Y-%m-%d"))
        
        # Apply payment method filter
        if payment_method:
            query = query.filter(OrderDB.payment_type == payment_method)
        
        # Apply order type filter
        if order_type:
            if order_type == "custom":
                query = query.join(OrderItemDB).filter(OrderItemDB.is_custom_order == True)
            elif order_type == "standard":
                query = query.join(OrderItemDB).filter(OrderItemDB.is_custom_order == False)
        
        # Apply pagination
        orders = query.offset(skip).limit(limit).all()
        
        # Convert to response format
        result = []
        for order in orders:
            order_items = db.query(OrderItemDB).filter(OrderItemDB.order_id == order.id).all()
            
            # Determine order type
            is_custom_order = any(item.is_custom_order for item in order_items)
            order_type_display = "custom" if is_custom_order else "standard"
            
            # Format items
            items = []
            for item in order_items:
                items.append({
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "subtotal": item.subtotal,
                    "is_custom_order": item.is_custom_order,
                    "is_free_ingredient": item.is_free_ingredient
                })
            
            result.append({
                "id": order.id,
                "order_type": order_type_display,
                "customer_name": order.customer_name,
                "customer_contact": order.customer_contact,
                "delivery_type": order.delivery_type,
                "hostel": order.hostel,
                "payment_type": order.payment_type,
                "delivery_fee": order.delivery_fee,
                "special_notes": order.special_notes,
                "items": items,
                "total": order.total,
                "order_date": order.order_date,
                "order_time": order.order_time,
                "created_by": order.created_by,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat()
            })
        
        return {
            "success": True,
            "data": result,
            "total_count": len(result)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching sales orders: {str(e)}"
        )

@router.get("/export", status_code=status.HTTP_200_OK)
async def export_sales_data(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    period: str = Query("day", description="Time period: day, week, month"),
    format: str = Query("csv", description="Export format: csv, json"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Export sales data in CSV or JSON format"""
    try:
        # Build base query
        query = db.query(OrderDB)
        
        # Apply date filters
        if start_date and end_date:
            query = query.filter(OrderDB.order_date >= start_date, OrderDB.order_date <= end_date)
        elif start_date:
            start_dt, end_dt = get_date_range(start_date, period)
            query = query.filter(OrderDB.order_date >= start_dt.strftime("%Y-%m-%d"), 
                               OrderDB.order_date <= end_dt.strftime("%Y-%m-%d"))
        
        orders = query.all()
        
        if format.lower() == "csv":
            # Generate CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            headers = ['Order ID', 'Date', 'Customer', 'Contact', 'Items', 'Total', 'Payment Method', 'Delivery Type', 'Order Type']
            writer.writerow(headers)
            
            # Write data
            for order in orders:
                order_items = db.query(OrderItemDB).filter(OrderItemDB.order_id == order.id).all()
                
                # Determine order type
                is_custom_order = any(item.is_custom_order for item in order_items)
                order_type_display = "Custom" if is_custom_order else "Standard"
                
                # Format items
                items_str = "; ".join([f"{item.product_name} ({item.quantity})" for item in order_items])
                
                writer.writerow([
                    order.id,
                    order.order_date,
                    order.customer_name,
                    order.customer_contact,
                    items_str,
                    f"{order.total:.2f}",
                    get_payment_method_display(order.payment_type),
                    order.delivery_type,
                    order_type_display
                ])
            
            output.seek(0)
            
            # Generate filename
            date_range = start_date if start_date else "all-dates"
            filename = f"sales-report-{period}-{date_range}.csv"
            
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8')),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        else:  # JSON format
            # Convert to JSON format
            result = []
            for order in orders:
                order_items = db.query(OrderItemDB).filter(OrderItemDB.order_id == order.id).all()
                
                # Determine order type
                is_custom_order = any(item.is_custom_order for item in order_items)
                order_type_display = "custom" if is_custom_order else "standard"
                
                # Format items
                items = []
                for item in order_items:
                    items.append({
                        "product_name": item.product_name,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "subtotal": item.subtotal
                    })
                
                result.append({
                    "order_id": order.id,
                    "date": order.order_date,
                    "customer_name": order.customer_name,
                    "customer_contact": order.customer_contact,
                    "items": items,
                    "total": order.total,
                    "payment_method": get_payment_method_display(order.payment_type),
                    "delivery_type": order.delivery_type,
                    "order_type": order_type_display
                })
            
            # Generate filename
            date_range = start_date if start_date else "all-dates"
            filename = f"sales-report-{period}-{date_range}.json"
            
            return StreamingResponse(
                io.BytesIO(json.dumps(result, indent=2).encode('utf-8')),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting sales data: {str(e)}"
        )
