from pydantic import BaseModel, EmailStr
from typing import Optional, List
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
    category: str
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
    category: Optional[str] = None
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
    packagingCost: float = 0.0
    overheadCost: float = 0.0
    ingredients: List[RecipeIngredient]
    totalCost: float
    costPerUnit: float

class RecipeCreate(RecipeBase):
    pass

class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    yieldQuantity: Optional[float] = None
    yieldUnitLabel: Optional[str] = None
    packagingCost: Optional[float] = None
    overheadCost: Optional[float] = None
    ingredients: Optional[List[RecipeIngredient]] = None
    totalCost: Optional[float] = None
    costPerUnit: Optional[float] = None

class Recipe(RecipeBase):
    id: str
    class Config:
        from_attributes = True

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int
