from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
import uuid
import json
from datetime import datetime

from ..database import get_db
from ..models_sqlalchemy import Order as OrderDB, OrderItem as OrderItemDB, Product as ProductDB, PackagingType as PackagingTypeDB
from ..auth import get_current_admin

router = APIRouter(
    prefix="/custom-orders",
    tags=["custom-orders"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_custom_order(
    order_data: dict,  # Accept raw JSON to match frontend structure exactly
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Create a custom order from the custom order form"""
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
            
            # Prepare custom details as JSON string
            custom_details_json = None
            if order_data.get("colour") or order_data.get("inscription") or order_data.get("additionalPrice") or order_data.get("totalCost"):
                custom_details_json = json.dumps({
                    "base_price": item["unitPrice"],
                    "additional_price": order_data.get("additionalPrice", 0.0),
                    "total_cost": order_data.get("totalCost", 0.0),
                    "colors": order_data.get("colour", ""),
                    "inscription": order_data.get("inscription", "")
                })
            
            # Create order item (custom order)
            db_item = OrderItemDB(
                id=item_id,
                order_id=db_order.id,
                product_id=item["productId"],
                product_name=item["productName"],
                quantity=item["quantity"],
                unit_price=item["unitPrice"],
                subtotal=item["subtotal"],
                is_custom_order=True,
                is_free_ingredient=False,
                custom_details=custom_details_json
            )
            
            db.add(db_item)
            
            # For custom orders, we don't update product quantities since they're custom made
            # But we can still validate the product/package exists
            product = db.query(ProductDB).filter(ProductDB.id == item["productId"]).first()
            if not product:
                # Try to find as package
                package = db.query(PackagingTypeDB).filter(PackagingTypeDB.id == item["productId"]).first()
                if not package:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Product or Package with ID {item['productId']} not found"
                    )
        
        # Commit all changes
        db.commit()
        db.refresh(db_order)
        
        return {
            "success": True,
            "message": "Custom order created successfully",
            "order_id": order_id,
            "total": order_data["total"],
            "custom_details": {
                "colour": order_data.get("colour"),
                "inscription": order_data.get("inscription"),
                "additional_price": order_data.get("additionalPrice", 0.0),
                "total_cost": order_data.get("totalCost", 0.0)
            }
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating custom order: {str(e)}"
        )

@router.get("/", status_code=status.HTTP_200_OK)
async def get_custom_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get all custom orders with pagination"""
    try:
        # Get only custom orders (where at least one item is custom)
        orders = db.query(OrderDB).join(OrderItemDB).filter(OrderItemDB.is_custom_order == True).offset(skip).limit(limit).all()
        
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
            detail=f"Error fetching custom orders: {str(e)}"
        )
