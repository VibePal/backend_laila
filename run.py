#!/usr/bin/env python3
"""
Simple script to run the Staff Management System FastAPI application.
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get configuration from environment variables or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = False
    
    print(f"Starting Staff Management System...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Reload: {reload}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"ReDoc: http://{host}:{port}/redoc")
    print(f"Health Check: http://{host}:{port}/health")
    print(f"Setup Endpoint: http://{host}:{port}/setup")
    print("-" * 50)
    print("IMPORTANT: Use POST /api/v1/auth/setup-admin to create initial admin account")
    print("Default credentials: admin / admin123 (change immediately!)")
    print("-" * 50)
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
