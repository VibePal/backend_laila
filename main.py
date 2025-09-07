from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="FastAPI Project",
    description="A modern FastAPI project with authentication and CRUD operations",
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

# Security
security = HTTPBearer()

# Pydantic models
class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: float

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    owner_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# In-memory storage (replace with database in production)
users_db = {}
items_db = {}
user_id_counter = 1
item_id_counter = 1

# Helper functions
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # This is a simplified authentication - implement proper JWT validation in production
    token = credentials.credentials
    # In production, validate JWT token here
    if token not in users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return users_db[token]

# Routes
@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI Project!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    global user_id_counter
    
    # Check if username or email already exists
    for existing_user in users_db.values():
        if existing_user["username"] == user.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        if existing_user["email"] == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create user (in production, hash the password)
    user_data = user.dict()
    user_data["id"] = user_id_counter
    user_data["is_active"] = True
    user_data["created_at"] = datetime.now()
    
    # Generate a simple token (replace with proper JWT in production)
    token = f"token_{user_id_counter}"
    users_db[token] = user_data
    
    user_id_counter += 1
    
    return User(**user_data)

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return User(**current_user)

@app.post("/login", response_model=Token)
async def login(username: str, password: str):
    # Find user by username and password (in production, verify hashed password)
    for token, user in users_db.items():
        if user["username"] == username and user["password"] == password:
            return {"access_token": token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.post("/items/", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate, current_user: dict = Depends(get_current_user)):
    global item_id_counter
    
    item_data = item.dict()
    item_data["id"] = item_id_counter
    item_data["owner_id"] = current_user["id"]
    item_data["created_at"] = datetime.now()
    
    items_db[item_id_counter] = item_data
    item_id_counter += 1
    
    return Item(**item_data)

@app.get("/items/", response_model=List[Item])
async def read_items(skip: int = 0, limit: int = 100):
    items = list(items_db.values())[skip : skip + limit]
    return [Item(**item) for item in items]

@app.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: int):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return Item(**items_db[item_id])

@app.put("/items/{item_id}", response_model=Item)
async def update_item(
    item_id: int, 
    item: ItemCreate, 
    current_user: dict = Depends(get_current_user)
):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if items_db[item_id]["owner_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    item_data = item.dict()
    item_data["id"] = item_id
    item_data["owner_id"] = current_user["id"]
    item_data["created_at"] = items_db[item_id]["created_at"]
    
    items_db[item_id] = item_data
    return Item(**item_data)

@app.delete("/items/{item_id}")
async def delete_item(item_id: int, current_user: dict = Depends(get_current_user)):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if items_db[item_id]["owner_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    del items_db[item_id]
    return {"message": "Item deleted successfully"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
