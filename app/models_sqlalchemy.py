# models_sqlalchemy.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# ---------------------------
# Staff
# ---------------------------
class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    fullName = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    role = Column(String, default="staff")  # could also use Enum
    isActive = Column(Boolean, default=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    payments = relationship("StaffPayment", back_populates="staff")


class StaffPayment(Base):
    __tablename__ = "staff_payments"

    id = Column(Integer, primary_key=True, index=True)
    staffId = Column(Integer, ForeignKey("staff.id"), nullable=False)
    amount = Column(Float, nullable=False)
    paymentDate = Column(DateTime, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    staff = relationship("Staff", back_populates="payments")

# ---------------------------
# Suppliers
# ---------------------------
class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    contact = Column(String, nullable=True)
    address = Column(Text, nullable=True)

# ---------------------------
# Items
# ---------------------------
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    unit = Column(String, nullable=False)

# ---------------------------
# Packaging Types
# ---------------------------
class PackagingType(Base):
    __tablename__ = "packaging_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)

# ---------------------------
# Overhead Cost Types
# ---------------------------
class OverheadCostType(Base):
    __tablename__ = "overhead_cost_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

# ---------------------------
# Supply Expenses
# ---------------------------
class SupplyExpense(Base):
    __tablename__ = "supply_expenses"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    supplier = Column(String, nullable=False)  # could be a FK if needed
    items = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    costPerItem = Column(Float, nullable=False)
    category = Column(String, default="Supply")
    purchaseUnit = Column(String, nullable=True)
    packageSize = Column(Float, nullable=True)
    total = Column(Float, nullable=False)
    pricePerUnit = Column(Float, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

# ---------------------------
# Products
# ---------------------------
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    unitPrice = Column(Float, nullable=False)
    costPerUnit = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    isAvailable = Column(Boolean, default=True)
    isActive = Column(Boolean, default=True)
    date = Column(DateTime, nullable=False)

# ---------------------------
# Recipes
# ---------------------------
class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    yieldQuantity = Column(Float, nullable=False)
    yieldUnitLabel = Column(String, nullable=False)
    ingredients = Column(Text, nullable=False)  # JSON string
    totalCost = Column(Float, nullable=False)
    costPerUnit = Column(Float, nullable=False)

# ---------------------------
# Orders
# ---------------------------
class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    customer_contact = Column(String, nullable=False)
    delivery_type = Column(String, nullable=False)  # "delivery" or "pickup"
    hostel = Column(String, nullable=True)
    payment_type = Column(String, nullable=False)  # "cash" or "momo"
    delivery_fee = Column(Float, default=0.0)
    special_notes = Column(Text, nullable=True)
    total = Column(Float, nullable=False)
    order_date = Column(String, nullable=False)
    order_time = Column(String, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    product_id = Column(String, nullable=False)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    is_custom_order = Column(Boolean, default=False)
    is_free_ingredient = Column(Boolean, default=False)
    custom_details = Column(Text, nullable=True)  # JSON string for custom order details
    created_at = Column(DateTime, default=datetime.utcnow)

# ---------------------------
# Overhead Costs
# ---------------------------
class OverheadCost(Base):
    __tablename__ = "overhead_costs"

    id = Column(String, primary_key=True, index=True)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(String, nullable=False)  # Stored as string in YYYY-MM-DD format
    recurring = Column(Boolean, default=False)
    frequency = Column(String, nullable=True)  # "Monthly", "Quarterly", "Annually", "One-time"
    cost_type = Column(String, nullable=False, default="operational")  # "operational" or "packaging"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
