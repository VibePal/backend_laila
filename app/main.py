from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import staff, payments, auth, suppliers, items, packaging_types, overhead_cost_types, supply_expenses, products, recipes, orders, custom_orders, overhead_costs, sales, financial
import os
from dotenv import load_dotenv

from .database import engine, Base
from . import models_sqlalchemy

Base.metadata.create_all(bind=engine)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Staff Management System",
    description="A comprehensive staff management and payment system API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:8080",
        "http://localhost:9001",
        "https://localhost:3000",
        "https://localhost:3001",
        "https://localhost:8080", 
        "https://localhost:9001",
        "https://laila-frontend-five.vercel.app"
        
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=["*"],  # Expose all headers to handle redirects
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(staff.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(suppliers.router, prefix="/api/v1")
app.include_router(items.router, prefix="/api/v1")
app.include_router(packaging_types.router, prefix="/api/v1")
app.include_router(overhead_cost_types.router, prefix="/api/v1")
app.include_router(supply_expenses.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(recipes.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(custom_orders.router, prefix="/api/v1")
app.include_router(overhead_costs.router, prefix="/api/v1")
app.include_router(sales.router, prefix="/api/v1")
app.include_router(financial.router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Staff Management System!", 
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# CORS test endpoint
@app.options("/api/v1/cors-test")
async def cors_test_options():
    return {"message": "CORS preflight successful"}

@app.get("/api/v1/cors-test")
async def cors_test():
    return {
        "message": "CORS is working!",
        "timestamp": "2024-01-01T00:00:00Z",
        "allowed_origins": [
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://localhost:8080",
            "http://localhost:9001"
        ]
    }

# Auth CORS preflight handlers
@app.options("/api/v1/auth/login")
async def auth_login_options():
    return {"message": "CORS preflight for login successful"}

@app.options("/api/v1/auth/signup")
async def auth_signup_options():
    return {"message": "CORS preflight for signup successful"}

@app.options("/api/v1/auth/refresh")
async def auth_refresh_options():
    return {"message": "CORS preflight for refresh successful"}

# Orders CORS preflight handlers
@app.options("/api/v1/orders/standard")
async def orders_standard_options():
    return {"message": "CORS preflight for standard order creation successful"}

@app.options("/api/v1/custom-orders/")
async def custom_orders_create_options():
    return {"message": "CORS preflight for custom order creation successful"}

@app.options("/api/v1/orders/{order_id}")
async def orders_options():
    return {"message": "CORS preflight for order operations successful"}

@app.options("/api/v1/auth/verify-password")
async def auth_verify_password_options():
    return {"message": "CORS preflight for password verification successful"}

@app.options("/api/v1/packaging-types/")
async def packaging_types_options():
    return {"message": "CORS preflight for packaging types successful"}

# API info endpoint
@app.get("/api/info")
async def api_info():
    return {
        "name": "Staff Management System",
        "version": "1.0.0",
        "description": "A comprehensive staff management and payment system API",
        "endpoints": {
            "authentication": "/api/v1/auth",
            "password_verification": "/api/v1/auth/verify-password",
            "staff": "/api/v1/staff",
            "payments": "/api/v1/payments",
            "suppliers": "/api/v1/suppliers",
            "items": "/api/v1/items",
            "packaging_types": "/api/v1/packaging-types",
            "overhead_cost_types": "/api/v1/overhead-cost-types",
            "supply_expenses": "/api/v1/supply-expenses",
            "products": "/api/v1/products",
            "recipes": "/api/v1/recipes",
            "orders": "/api/v1/orders",
            "order_update": "/api/v1/orders/{order_id}",
            "all_orders": "/api/v1/orders/all",
            "custom_orders": "/api/v1/custom-orders",
            "overhead_costs": "/api/v1/overhead-costs",
            "sales": "/api/v1/sales",
            "financial": "/api/v1/financial"
        }
    }

# Setup endpoint for initial admin creation
@app.post("/setup")
async def setup_system():
    """Setup the system with initial admin account."""
    return {
        "message": "System setup endpoint",
        "instructions": "Use POST /api/v1/auth/setup-admin to create the first admin account"
    }