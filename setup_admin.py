#!/usr/bin/env python3
"""
Setup script to create the initial admin account for the Staff Management System.
"""

import requests
import json
import sys

def setup_admin(base_url="http://localhost:8000"):
    """Setup the initial admin account."""
    
    print("Setting up Staff Management System...")
    print(f"API Base URL: {base_url}")
    print("-" * 50)
    
    # Test if the server is running
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server health check failed")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on", base_url)
        return False
    
    # Create admin account
    try:
        response = requests.post(f"{base_url}/api/v1/auth/setup-admin")
        
        if response.status_code == 201:
            admin_data = response.json()
            print("✅ Admin account created successfully!")
            print(f"   Username: {admin_data['username']}")
            print(f"   Full Name: {admin_data['fullName']}")
            print(f"   Role: {admin_data['role']}")
            print(f"   ID: {admin_data['id']}")
            print("\n⚠️  IMPORTANT: Change the default password immediately!")
            print("   Default password: admin123")
            print("\n🔗 You can now login at:")
            print(f"   {base_url}/docs")
            return True
        else:
            print(f"❌ Failed to create admin account: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating admin account: {e}")
        return False

def test_login(base_url="http://localhost:8000"):
    """Test the admin login."""
    
    print("\nTesting admin login...")
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/auth/login",
            data={
                "username": "admin",
                "password": "admin123"
            }
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Login successful!")
            print(f"   Access Token: {token_data['access_token'][:20]}...")
            print(f"   Token Type: {token_data['token_type']}")
            print(f"   Expires In: {token_data['expires_in']} seconds")
            return token_data['access_token']
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing login: {e}")
        return None

if __name__ == "__main__":
    # Check if base URL is provided as command line argument
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print("Staff Management System - Admin Setup")
    print("=" * 50)
    
    # Setup admin account
    if setup_admin(base_url):
        # Test login
        token = test_login(base_url)
        
        if token:
            print("\n🎉 Setup completed successfully!")
            print("\nNext steps:")
            print("1. Change the default admin password")
            print("2. Create additional staff members")
            print("3. Start managing your staff and payments")
            print(f"\n🔗 Access the API documentation at: {base_url}/docs")
        else:
            print("\n⚠️  Setup completed but login test failed")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)
