from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
import uuid
import json
from datetime import datetime

from app.database import get_db
from app.models_sqlalchemy import Order as OrderDB, OrderItem as OrderItemDB, Product as ProductDB, PackagingType as PackagingTypeDB
from app.auth import get_current_admin, get_current_staff_or_admin
from app.models import OrderUpdate

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    responses={404: {"description": "Not found"}},
)

@router.post("/standard", status_code=status.HTTP_201_CREATED)
async def create_standard_order(
    order_data: dict,  # Accept raw JSON to match frontend structure exactly
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_staff_or_admin)
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
            created_by=current_user.user_id
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
    current_user: dict = Depends(get_current_staff_or_admin)
):
    """Get all orders with pagination"""
    try:
        # Build query with role-based filtering
        query = db.query(OrderDB)
        
        # Apply role-based filtering
        if current_user.role == "staff":
            # Staff users can only see orders they created
            query = query.filter(OrderDB.created_by == current_user.user_id)
        # Admin users can see all orders (no additional filter)
        
        # Apply pagination
        orders = query.offset(skip).limit(limit).all()
        
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
    current_user: dict = Depends(get_current_staff_or_admin)
):
    """Get all orders (both standard and custom) with clear type indicators"""
    try:
        # Build query with role-based filtering
        query = db.query(OrderDB)
        
        # Apply role-based filtering
        if current_user.role == "staff":
            # Staff users can only see orders they created
            query = query.filter(OrderDB.created_by == current_user.user_id)
        # Admin users can see all orders (no additional filter)
        
        # Apply pagination
        orders = query.offset(skip).limit(limit).all()
        
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

@router.patch("/{order_id}", summary="Update Order")
async def update_order(
    order_id: str,
    order_update: dict,  # Accept raw JSON to match frontend structure
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_staff_or_admin)
):
    """Update an existing order"""
    try:
        # Find the order
        db_order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
        if not db_order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Check permissions - staff can only edit orders they created
        if current_user.role == "staff" and db_order.created_by != current_user.user_id:
            raise HTTPException(status_code=403, detail="Insufficient permissions to edit this order")
        
        # Update order fields
        if "customerName" in order_update:
            db_order.customer_name = order_update["customerName"]
        if "customerContact" in order_update:
            db_order.customer_contact = order_update["customerContact"]
        if "deliveryType" in order_update:
            db_order.delivery_type = order_update["deliveryType"]
        if "hostel" in order_update:
            db_order.hostel = order_update["hostel"]
        if "paymentType" in order_update:
            db_order.payment_type = order_update["paymentType"]
        if "deliveryFee" in order_update:
            db_order.delivery_fee = order_update["deliveryFee"]
        if "specialNotes" in order_update:
            db_order.special_notes = order_update["specialNotes"]
        if "total" in order_update:
            db_order.total = order_update["total"]
        if "orderDate" in order_update:
            db_order.order_date = order_update["orderDate"]
        if "orderTime" in order_update:
            db_order.order_time = order_update["orderTime"]
        
        # Set edited_by field
        db_order.edited_by = current_user.username
        db_order.updated_at = datetime.utcnow()
        
        # Update order items if provided
        if "items" in order_update:
            # Delete existing order items
            db.query(OrderItemDB).filter(OrderItemDB.order_id == order_id).delete()
            
            # Add new order items
            for item in order_update["items"]:
                item_id = f"ITEM-{int(datetime.now().timestamp() * 1000)}-{uuid.uuid4().hex[:8]}"
                
                # Handle custom details for custom orders
                custom_details_json = None
                if item.get("is_custom_order") and item.get("custom_details"):
                    custom_details = item["custom_details"]
                    custom_details_json = json.dumps({
                        "base_price": custom_details.get("base_price"),
                        "additional_price": custom_details.get("additional_price"),
                        "total_cost": custom_details.get("total_cost"),
                        "colors": custom_details.get("colors"),
                        "inscription": custom_details.get("inscription")
                    })
                
                db_item = OrderItemDB(
                    id=item_id,
                    order_id=order_id,
                    product_id=item["productId"],
                    product_name=item["productName"],
                    quantity=item["quantity"],
                    unit_price=item["unitPrice"],
                    subtotal=item["subtotal"],
                    is_custom_order=item.get("is_custom_order", False),
                    is_free_ingredient=item.get("is_free_ingredient", False),
                    custom_details=custom_details_json
                )
                db.add(db_item)
        
        db.commit()
        db.refresh(db_order)
        
        return {
            "success": True,
            "message": "Order updated successfully",
            "data": {
                "id": db_order.id,
                "updatedAt": db_order.updated_at.isoformat(),
                "editedBy": db_order.edited_by,
                "total": db_order.total
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating order: {str(e)}"
        )