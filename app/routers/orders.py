from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
import uuid
import json
from datetime import datetime

from ..database import get_db
from ..models_sqlalchemy import Order as OrderDB, OrderItem as OrderItemDB, Product as ProductDB, PackagingType as PackagingTypeDB
from ..auth import get_current_admin

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    responses={404: {"description": "Not found"}},
)

@router.post("/standard", status_code=status.HTTP_201_CREATED)
async def create_standard_order(
    order_data: dict,  # Accept raw JSON to match frontend structure exactly
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Create a standard order from the standard order form"""
    try:
        # Generate unique order ID
        order_id = f"ORD-{int(datetime.now().timestamp() * 1000)}"
        
        # Create the main order record
        db_order = OrderDB(
            id=order_id,
            customer_name=order_data["customerName"],
            customer_contact=order_data["customerContact"],
            delivery_type=order_data["deliveryType"],  # "delivery" or "pickup"
            hostel=order_data.get("hostel"),
            payment_type=order_data["paymentType"],  # "cash" or "momo"
            delivery_fee=order_data.get("deliveryFee", 0.0),
            special_notes=order_data.get("specialNotes"),
            total=order_data["total"],
            order_date=order_data["orderDate"],
            order_time=order_data["orderTime"],
            created_by=order_data["createdBy"]
        )
        
        db.add(db_order)
        db.flush()  # Flush to get the order ID
        
        # Process order items (products and packages)
        for item in order_data["items"]:
            # Generate unique item ID
            item_id = f"ITEM-{int(datetime.now().timestamp() * 1000)}-{uuid.uuid4().hex[:8]}"
            
            # Create order item (standard order - no custom details)
            db_item = OrderItemDB(
                id=item_id,
                order_id=db_order.id,
                product_id=item["productId"],
                product_name=item["productName"],
                quantity=item["quantity"],
                unit_price=item["unitPrice"],
                subtotal=item["subtotal"],
                is_custom_order=False,
                is_free_ingredient=False,
                custom_details=None
            )
            
            db.add(db_item)
            
            # Check if it's a product or package and handle accordingly
            # Try to find as product first
            product = db.query(ProductDB).filter(ProductDB.id == item["productId"]).first()
            if product:
                # It's a product - update inventory
                if product.quantity < item["quantity"]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient quantity for {product.name}. Available: {product.quantity}, Requested: {item['quantity']}"
                    )
                
                # Update product quantity
                product.quantity -= item["quantity"]
                db.add(product)
            else:
                # Try to find as package
                package = db.query(PackagingTypeDB).filter(PackagingTypeDB.id == item["productId"]).first()
                if not package:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Product or Package with ID {item['productId']} not found"
                    )
                # For packages, we don't update inventory, just validate it exists
        
        # Commit all changes
        db.commit()
        db.refresh(db_order)
        
        return {
            "success": True,
            "message": "Standard order created successfully",
            "order_id": order_id,
            "total": order_data["total"]
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating standard order: {str(e)}"
        )

@router.get("/", status_code=status.HTTP_200_OK)
async def get_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get all orders with pagination"""
    try:
        orders = db.query(OrderDB).offset(skip).limit(limit).all()
        
        result = []
        for order in orders:
            # Get order items
            order_items = db.query(OrderItemDB).filter(OrderItemDB.order_id == order.id).all()
            
            # Convert items to response format
            response_items = []
            for item in order_items:
                custom_details = None
                if item.custom_details:
                    try:
                        custom_details_dict = json.loads(item.custom_details)
                        custom_details = {
                            "base_price": custom_details_dict.get("base_price"),
                            "additional_price": custom_details_dict.get("additional_price"),
                            "total_cost": custom_details_dict.get("total_cost"),
                            "colors": custom_details_dict.get("colors"),
                            "inscription": custom_details_dict.get("inscription")
                        }
                    except json.JSONDecodeError:
                        custom_details = None
                
                response_items.append({
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "subtotal": item.subtotal,
                    "is_custom_order": item.is_custom_order,
                    "is_free_ingredient": item.is_free_ingredient,
                    "custom_details": custom_details
                })
            
            result.append({
                "id": order.id,
                "customer_name": order.customer_name,
                "customer_contact": order.customer_contact,
                "delivery_type": order.delivery_type,
                "hostel": order.hostel,
                "payment_type": order.payment_type,
                "delivery_fee": order.delivery_fee,
                "special_notes": order.special_notes,
                "items": response_items,
                "total": order.total,
                "order_date": order.order_date,
                "order_time": order.order_time,
                "created_by": order.created_by,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat()
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching orders: {str(e)}"
        )

@router.get("/all", status_code=status.HTTP_200_OK)
async def get_all_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get all orders (both standard and custom) with clear type indicators"""
    try:
        # Get all orders from the orders table
        orders = db.query(OrderDB).offset(skip).limit(limit).all()
        
        result = []
        for order in orders:
            # Get order items
            order_items = db.query(OrderItemDB).filter(OrderItemDB.order_id == order.id).all()
            
            # Determine if this is a custom order by checking if any item is marked as custom
            is_custom_order = any(item.is_custom_order for item in order_items)
            order_type = "custom" if is_custom_order else "standard"
            
            # Debug logging
            print(f"DEBUG: Order {order.id} - Items: {len(order_items)}, Custom items: {[item.is_custom_order for item in order_items]}, Type: {order_type}")
            
            # Convert items to response format
            response_items = []
            for item in order_items:
                custom_details = None
                if item.custom_details:
                    try:
                        custom_details_dict = json.loads(item.custom_details)
                        custom_details = {
                            "base_price": custom_details_dict.get("base_price"),
                            "additional_price": custom_details_dict.get("additional_price"),
                            "total_cost": custom_details_dict.get("total_cost"),
                            "colors": custom_details_dict.get("colors"),
                            "inscription": custom_details_dict.get("inscription")
                        }
                    except json.JSONDecodeError:
                        custom_details = None
                
                response_items.append({
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "subtotal": item.subtotal,
                    "is_custom_order": item.is_custom_order,
                    "is_free_ingredient": item.is_free_ingredient,
                    "custom_details": custom_details
                })
            
            result.append({
                "id": order.id,
                "order_type": order_type,  # "standard" or "custom"
                "customer_name": order.customer_name,
                "customer_contact": order.customer_contact,
                "delivery_type": order.delivery_type,
                "hostel": order.hostel,
                "payment_type": order.payment_type,
                "delivery_fee": order.delivery_fee,
                "special_notes": order.special_notes,
                "items": response_items,
                "total": order.total,
                "order_date": order.order_date,
                "order_time": order.order_time,
                "created_by": order.created_by,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat()
            })
        
        return {
            "orders": result,
            "total_count": len(result),
            "order_types": {
                "standard": len([o for o in result if o["order_type"] == "standard"]),
                "custom": len([o for o in result if o["order_type"] == "custom"])
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching all orders: {str(e)}"
        )