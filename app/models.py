from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

# Enums
class StaffRole(str, Enum):
    STAFF = "staff"
    ADMIN = "admin"

class ExpenseCategory(str, Enum):
    SUPPLY = "Supply"
    PACKAGING = "Packaging"
    OVERHEAD = "Overhead"

class DeliveryType(str, Enum):
    DELIVERY = "delivery"
    PICKUP = "pickup"

class PaymentType(str, Enum):
    CASH = "cash"
    MOMO = "momo"

# Staff Models
class StaffBase(BaseModel):
    fullName: str
    username: str
    role: StaffRole

class StaffCreate(StaffBase):
    password: str

class StaffUpdate(BaseModel):
    fullName: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[StaffRole] = None
    isActive: Optional[bool] = None

class Staff(StaffBase):
    id: str
    isActive: bool
    createdAt: str
    class Config:
        from_attributes = True

# Staff Payment Models
class StaffPaymentBase(BaseModel):
    staffId: str
    amount: float
    paymentDate: str

class StaffPaymentCreate(StaffPaymentBase):
    pass

class StaffPaymentUpdate(BaseModel):
    amount: Optional[float] = None
    paymentDate: Optional[str] = None

class StaffPayment(StaffPaymentBase):
    id: str
    staffName: str
    createdAt: str
    class Config:
        from_attributes = True

# Settings Models - Suppliers
class SupplierBase(BaseModel):
    name: str
    contact: Optional[str] = None
    address: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    address: Optional[str] = None

class Supplier(SupplierBase):
    id: str
    class Config:
        from_attributes = True

# Settings Models - Items
class ItemBase(BaseModel):
    name: str
    unit: str

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None

class Item(ItemBase):
    id: str
    class Config:
        from_attributes = True

# Settings Models - Packaging Types
class PackagingTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

class PackagingTypeCreate(PackagingTypeBase):
    pass

class PackagingTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None

class PackagingType(PackagingTypeBase):
    id: str
    class Config:
        from_attributes = True

# Settings Models - Overhead Cost Types
class OverheadCostTypeBase(BaseModel):
    name: str

class OverheadCostTypeCreate(OverheadCostTypeBase):
    pass

class OverheadCostTypeUpdate(BaseModel):
    name: Optional[str] = None

class OverheadCostType(OverheadCostTypeBase):
    id: str
    class Config:
        from_attributes = True

# Supply Expense Models
class SupplyExpenseBase(BaseModel):
    date: str
    supplier: str
    items: str
    quantity: int
    costPerItem: float
    category: ExpenseCategory = ExpenseCategory.SUPPLY
    purchaseUnit: Optional[str] = None
    packageSize: Optional[float] = None

class SupplyExpenseCreate(SupplyExpenseBase):
    pass

class SupplyExpenseUpdate(BaseModel):
    date: Optional[str] = None
    supplier: Optional[str] = None
    items: Optional[str] = None
    quantity: Optional[int] = None
    costPerItem: Optional[float] = None
    category: Optional[ExpenseCategory] = None
    purchaseUnit: Optional[str] = None
    packageSize: Optional[float] = None

class SupplyExpense(SupplyExpenseBase):
    id: str
    total: float
    pricePerUnit: Optional[float] = None
    createdAt: str
    class Config:
        from_attributes = True

# Authentication Models
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: Optional[int] = None

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[StaffRole] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class SignupRequest(BaseModel):
    username: str
    password: str

# Response Models
class MessageResponse(BaseModel):
    message: str
    success: bool = True

# Product Models
class ProductBase(BaseModel):
    name: str
    unitPrice: float
    costPerUnit: float
    quantity: int
    isAvailable: bool = True
    isActive: bool = True
    date: str

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    unitPrice: Optional[float] = None
    costPerUnit: Optional[float] = None
    quantity: Optional[int] = None
    isAvailable: Optional[bool] = None
    isActive: Optional[bool] = None
    date: Optional[str] = None

class Product(ProductBase):
    id: str
    class Config:
        from_attributes = True

# Recipe Models
class RecipeIngredient(BaseModel):
    ingredientId: str
    quantity: float
    unit: str  # 'kg' | 'g' | 'L' | 'ml' | 'piece'

class RecipeBase(BaseModel):
    name: str
    yieldQuantity: float
    yieldUnitLabel: str
    ingredients: List[RecipeIngredient]
    totalCost: float
    costPerUnit: float

class RecipeCreate(RecipeBase):
    pass

class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    yieldQuantity: Optional[float] = None
    yieldUnitLabel: Optional[str] = None
    ingredients: Optional[List[RecipeIngredient]] = None
    totalCost: Optional[float] = None
    costPerUnit: Optional[float] = None

class Recipe(RecipeBase):
    id: str
    class Config:
        from_attributes = True

# Order Models
class CustomOrderDetails(BaseModel):
    base_price: float
    additional_price: float
    colors: Optional[str] = None
    inscription: Optional[str] = None

class OrderItemBase(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float
    is_custom_order: bool = False
    is_free_ingredient: bool = False
    custom_details: Optional[CustomOrderDetails] = None

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: str
    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    customer_name: str
    customer_contact: str
    delivery_type: DeliveryType
    hostel: Optional[str] = None
    payment_type: PaymentType
    delivery_fee: float = 0.0
    special_notes: Optional[str] = None
    items: List[OrderItemCreate]
    total: float
    order_date: str
    order_time: str
    created_by: str

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_contact: Optional[str] = None
    delivery_type: Optional[DeliveryType] = None
    hostel: Optional[str] = None
    payment_type: Optional[PaymentType] = None
    delivery_fee: Optional[float] = None
    special_notes: Optional[str] = None
    total: Optional[float] = None
    order_date: Optional[str] = None
    order_time: Optional[str] = None

class Order(OrderBase):
    id: str
    created_at: str
    updated_at: str
    items: List[OrderItem]
    class Config:
        from_attributes = True

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int

# ---------------------------
# Overhead Costs
# ---------------------------
class OverheadCostBase(BaseModel):
    category: str
    description: str
    amount: float
    date: str
    recurring: bool = False
    frequency: Optional[str] = None
    cost_type: str = "operational"  # "operational" or "packaging"

class OverheadCostCreate(OverheadCostBase):
    pass

class OverheadCostUpdate(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[str] = None
    recurring: Optional[bool] = None
    frequency: Optional[str] = None
    cost_type: Optional[str] = None

class OverheadCost(OverheadCostBase):
    id: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True

# ---------------------------
# Sales Analytics
# ---------------------------
class SalesSummary(BaseModel):
    total_orders: int
    total_sales: float
    total_revenue: float
    date_range: str
    period: str

class PaymentBreakdown(BaseModel):
    payment_method: str
    amount: float
    percentage: float
    count: int

class ProductBreakdown(BaseModel):
    product_category: str
    amount: float
    percentage: float
    count: int

class SalesBreakdown(BaseModel):
    payment_methods: List[PaymentBreakdown]
    product_categories: List[ProductBreakdown]

class SalesFilter(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    period: Optional[str] = "day"  # "day", "week", "month"
    payment_method: Optional[str] = None
    product_category: Optional[str] = None
    order_type: Optional[str] = None  # "standard", "custom"

class SalesExportRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    period: Optional[str] = "day"
    format: str = "csv"  # "csv", "json"
    include_details: bool = True

# ---------------------------
# Financial Analytics
# ---------------------------
class FinancialSummary(BaseModel):
    total_revenue: float
    total_orders: int
    supply_expenses: float
    staff_payments: float
    overhead_costs: float
    total_expenses: float
    net_profit: float
    date_range: str
    period: str

class RevenueBreakdown(BaseModel):
    total_revenue: float
    total_orders: int
    average_order_value: float
    revenue_by_payment_method: Dict[str, float]
    revenue_by_order_type: Dict[str, float]

class ExpenseBreakdown(BaseModel):
    supply_expenses: float
    staff_payments: float
    overhead_costs: float
    total_expenses: float
    expense_categories: Dict[str, float]

class ProfitAnalysis(BaseModel):
    net_profit: float
    profit_margin: float
    revenue: float
    expenses: float
    profitability_ratio: float

class FinancialBreakdown(BaseModel):
    revenue: RevenueBreakdown
    expenses: ExpenseBreakdown
    profit: ProfitAnalysis

class FinancialFilter(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    period: Optional[str] = "day"  # "day", "week", "month"
    include_overhead: bool = True
    include_staff_payments: bool = True
