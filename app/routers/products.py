from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from ..models import Product, ProductCreate, ProductUpdate
from ..models_sqlalchemy import Product as ProductDB
from ..database import get_db
from ..auth import get_current_admin, get_current_staff_or_admin

router = APIRouter(prefix="/products", tags=["products"])

# Test endpoint without authentication to verify CORS
@router.get("/test", summary="Test CORS")
async def test_cors():
    """Test endpoint to verify CORS is working"""
    return {
        "message": "CORS is working!",
        "timestamp": datetime.now().isoformat(),
        "status": "success"
    }

# Test endpoint with authentication to debug auth issues
@router.get("/test-auth", summary="Test Authentication")
async def test_auth(current_admin: dict = Depends(get_current_admin)):
    """Test endpoint to verify authentication is working"""
    return {
        "message": "Authentication is working!",
        "user": current_admin,
        "timestamp": datetime.now().isoformat(),
        "status": "success"
    }


@router.post("/", response_model=Product, summary="Create Product")
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new product"""
    try:
        product_date = datetime.fromisoformat(product.date.replace('Z', '+00:00'))
        
        # Check if category column exists in database (temporary fix)
        try:
            # Try to create product without category
            db_product = ProductDB(
                name=product.name,
                unitPrice=product.unitPrice,
                costPerUnit=product.costPerUnit,
                quantity=product.quantity,
                isAvailable=product.isAvailable,
                isActive=product.isActive,
                date=product_date
            )
        except Exception as db_error:
            if "category" in str(db_error) and "not-null constraint" in str(db_error):
                # Database still has old schema with category column
                raise HTTPException(
                    status_code=500,
                    detail="Database schema needs to be updated. Please run the migration script: python migrate_remove_category.py"
                )
            else:
                raise db_error
        
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        
        return Product(
            id=str(db_product.id),
            name=db_product.name,
            unitPrice=db_product.unitPrice,
            costPerUnit=db_product.costPerUnit,
            quantity=db_product.quantity,
            isAvailable=db_product.isAvailable,
            isActive=db_product.isActive,
            date=product.date
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating product: {str(e)}"
        )

@router.get("/", response_model=List[Product], summary="Get All Products")
async def get_products(
    date: Optional[str] = Query(None, description="Filter by specific date (YYYY-MM-DD)"),
    isActive: Optional[bool] = Query(None, description="Filter by active status"),
    isAvailable: Optional[bool] = Query(None, description="Filter by availability"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_staff_or_admin)
):
    """Get all products with optional filtering"""
    query = db.query(ProductDB)
    
    # Apply filters
    if date:
        filter_date = datetime.fromisoformat(date)
        query = query.filter(ProductDB.date == filter_date)
    if isActive is not None:
        query = query.filter(ProductDB.isActive == isActive)
    if isAvailable is not None:
        query = query.filter(ProductDB.isAvailable == isAvailable)
    
    db_products = query.all()
    
    products = []
    for product in db_products:
        products.append(Product(
            id=str(product.id),
            name=product.name,
            unitPrice=product.unitPrice,
            costPerUnit=product.costPerUnit,
            quantity=product.quantity,
            isAvailable=product.isAvailable,
            isActive=product.isActive,
            date=product.date.isoformat()
        ))
    
    return products

@router.get("/{product_id}", response_model=Product, summary="Get Product by ID")
async def get_product(product_id: str, db: Session = Depends(get_db)):
    """Get a specific product by ID"""
    db_product = db.query(ProductDB).filter(ProductDB.id == int(product_id)).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return Product(
        id=str(db_product.id),
        name=db_product.name,
        unitPrice=db_product.unitPrice,
        costPerUnit=db_product.costPerUnit,
        quantity=db_product.quantity,
        isAvailable=db_product.isAvailable,
        isActive=db_product.isActive,
        date=db_product.date.isoformat()
    )

@router.get("/by-date/{date}", response_model=List[Product], summary="Get Products by Date")
async def get_products_by_date(date: str, db: Session = Depends(get_db)):
    """Get all products for a specific date"""
    filter_date = datetime.fromisoformat(date)
    db_products = db.query(ProductDB).filter(ProductDB.date == filter_date).all()
    
    products = []
    for product in db_products:
        products.append(Product(
            id=str(product.id),
            name=product.name,
            unitPrice=product.unitPrice,
            costPerUnit=product.costPerUnit,
            quantity=product.quantity,
            isAvailable=product.isAvailable,
            isActive=product.isActive,
            date=product.date.isoformat()
        ))
    
    return products


@router.patch("/{product_id}", response_model=Product, summary="Update Product")
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Update a product"""
    db_product = db.query(ProductDB).filter(ProductDB.id == int(product_id)).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "date":
            setattr(db_product, field, datetime.fromisoformat(value.replace('Z', '+00:00')))
        else:
            setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    
    return Product(
        id=str(db_product.id),
        name=db_product.name,
        unitPrice=db_product.unitPrice,
        costPerUnit=db_product.costPerUnit,
        quantity=db_product.quantity,
        isAvailable=db_product.isAvailable,
        isActive=db_product.isActive,
        date=db_product.date.isoformat()
    )

@router.patch("/{product_id}/availability", response_model=Product, summary="Toggle Product Availability")
async def toggle_product_availability(
    product_id: str,
    isAvailable: bool,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Toggle product availability"""
    db_product = db.query(ProductDB).filter(ProductDB.id == int(product_id)).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db_product.isAvailable = isAvailable
    db.commit()
    db.refresh(db_product)
    
    return Product(
        id=str(db_product.id),
        name=db_product.name,
        unitPrice=db_product.unitPrice,
        costPerUnit=db_product.costPerUnit,
        quantity=db_product.quantity,
        isAvailable=db_product.isAvailable,
        isActive=db_product.isActive,
        date=db_product.date.isoformat()
    )

@router.delete("/{product_id}", summary="Delete Product")
async def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Delete a product"""
    db_product = db.query(ProductDB).filter(ProductDB.id == int(product_id)).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted successfully"}

@router.get("/summary/inventory", summary="Get Inventory Summary")
async def get_inventory_summary(
    date: Optional[str] = Query(None, description="Filter by specific date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get inventory summary statistics"""
    from sqlalchemy import func
    
    query = db.query(ProductDB)
    
    if date:
        filter_date = datetime.fromisoformat(date)
        query = query.filter(ProductDB.date == filter_date)
    
    # Get aggregated data
    result = query.with_entities(
        func.count(ProductDB.id).label('total_products'),
        func.sum(ProductDB.unitPrice * ProductDB.quantity).label('total_value'),
        func.avg(ProductDB.unitPrice).label('avg_unit_price')
    ).first()
    
    # Count available/unavailable products
    available_count = query.filter(ProductDB.isAvailable == True).count()
    unavailable_count = query.filter(ProductDB.isAvailable == False).count()
    
    total_products = result.total_products or 0
    total_value = result.total_value or 0.0
    avg_unit_price = result.avg_unit_price or 0.0
    
    return {
        "totalProducts": total_products,
        "totalValue": round(total_value, 2),
        "availableProducts": available_count,
        "unavailableProducts": unavailable_count,
        "averageUnitPrice": round(avg_unit_price, 2)
    }
