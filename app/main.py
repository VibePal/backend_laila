from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import staff, payments, auth, suppliers, items, packaging_types, overhead_cost_types, supply_expenses, products, recipes
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
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# API info endpoint
@app.get("/api/info")
async def api_info():
    return {
        "name": "Staff Management System",
        "version": "1.0.0",
        "description": "A comprehensive staff management and payment system API",
        "endpoints": {
            "authentication": "/api/v1/auth",
            "staff": "/api/v1/staff",
            "payments": "/api/v1/payments",
            "suppliers": "/api/v1/suppliers",
            "items": "/api/v1/items",
            "packaging_types": "/api/v1/packaging-types",
            "overhead_cost_types": "/api/v1/overhead-cost-types",
            "supply_expenses": "/api/v1/supply-expenses",
            "products": "/api/v1/products",
            "recipes": "/api/v1/recipes"
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
