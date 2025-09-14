from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool, NullPool
import os
from dotenv import load_dotenv
# from sqlalchemy.pool import 

load_dotenv()

# Database URL from environment variable or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine based on database type
if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set. Please check your .env file.")
    # For PostgreSQL and other databases
    if "postgresql" in DATABASE_URL:
        engine = create_engine(
            DATABASE_URL,
            poolclass=NullPool,  # No connection pooling for serverless
            connect_args={"sslmode": "require"}
        )
    else:
        engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database models (for future use)
# from .models import User, Item
# Base.metadata.create_all(bind=engine)
