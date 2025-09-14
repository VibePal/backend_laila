#!/usr/bin/env python3
"""
Migration script to remove the 'category' column from the products table.
This fixes the NOT NULL constraint violation when creating products.
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

load_dotenv()

def run_migration():
    """Remove the category column from products table"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL environment variable is not set")
        return False
    
    try:
        # Create engine
        if DATABASE_URL.startswith("sqlite"):
            engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        else:
            engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            # Check if category column exists
            if DATABASE_URL.startswith("sqlite"):
                # SQLite syntax
                result = connection.execute(text("""
                    PRAGMA table_info(products);
                """))
                columns = [row[1] for row in result.fetchall()]
                
                if 'category' in columns:
                    print("🔍 Found 'category' column in products table")
                    # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
                    print("📝 SQLite detected - recreating products table without category column...")
                    
                    # Create new table without category column
                    connection.execute(text("""
                        CREATE TABLE products_new (
                            id INTEGER PRIMARY KEY,
                            name VARCHAR NOT NULL,
                            "unitPrice" FLOAT NOT NULL,
                            "costPerUnit" FLOAT NOT NULL,
                            quantity INTEGER NOT NULL,
                            "isAvailable" BOOLEAN DEFAULT true,
                            "isActive" BOOLEAN DEFAULT true,
                            date DATETIME NOT NULL
                        );
                    """))
                    
                    # Copy data from old table to new table
                    connection.execute(text("""
                        INSERT INTO products_new (id, name, "unitPrice", "costPerUnit", quantity, "isAvailable", "isActive", date)
                        SELECT id, name, "unitPrice", "costPerUnit", quantity, "isAvailable", "isActive", date
                        FROM products;
                    """))
                    
                    # Drop old table and rename new table
                    connection.execute(text("DROP TABLE products;"))
                    connection.execute(text("ALTER TABLE products_new RENAME TO products;"))
                    
                    print("✅ Successfully recreated products table without category column")
                else:
                    print("✅ Category column not found - no migration needed")
                    
            else:
                # PostgreSQL syntax
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'products' AND column_name = 'category';
                """))
                
                if result.fetchone():
                    print("🔍 Found 'category' column in products table")
                    print("📝 Removing category column...")
                    
                    # Drop the category column
                    connection.execute(text("ALTER TABLE products DROP COLUMN category;"))
                    connection.commit()
                    
                    print("✅ Successfully removed category column from products table")
                else:
                    print("✅ Category column not found - no migration needed")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting migration to remove category column from products table...")
    success = run_migration()
    
    if success:
        print("🎉 Migration completed successfully!")
        print("💡 You can now create products without the category field")
    else:
        print("💥 Migration failed. Please check the error messages above.")
        sys.exit(1)
