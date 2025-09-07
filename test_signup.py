#!/usr/bin/env python3
"""
Simple test script to verify the signup endpoint functionality.
"""

import requests
import json

def test_signup_endpoint():
    """Test the signup endpoint with sample data."""
    base_url = "http://localhost:8000"
    signup_url = f"{base_url}/api/v1/auth/signup"
    
    # Test data
    test_user = {
        "username": "testadmin",
        "password": "testpassword123"
    }
    
    print("Testing signup endpoint...")
    print(f"URL: {signup_url}")
    print(f"Data: {json.dumps(test_user, indent=2)}")
    print("-" * 50)
    
    try:
        # Make the request
        response = requests.post(
            signup_url,
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 201:
            print("✅ Signup successful!")
            response_data = response.json()
            print(f"Created user: {json.dumps(response_data, indent=2)}")
            
            # Verify the user has admin role
            if response_data.get("role") == "admin":
                print("✅ User correctly assigned admin role!")
            else:
                print(f"❌ User role is {response_data.get('role')}, expected 'admin'")
                
        else:
            print("❌ Signup failed!")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server.")
        print("Make sure the server is running on http://localhost:8000")
        print("Run: python run.py")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_duplicate_username():
    """Test signup with duplicate username."""
    base_url = "http://localhost:8000"
    signup_url = f"{base_url}/api/v1/auth/signup"
    
    # Try to create the same user again
    test_user = {
        "username": "testadmin",
        "password": "differentpassword"
    }
    
    print("\nTesting duplicate username...")
    print(f"URL: {signup_url}")
    print(f"Data: {json.dumps(test_user, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(
            signup_url,
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ Correctly rejected duplicate username!")
            print(f"Error message: {response.json().get('detail', 'No detail provided')}")
        else:
            print("❌ Should have rejected duplicate username!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("SIGNUP ENDPOINT TEST")
    print("=" * 60)
    
    test_signup_endpoint()
    test_duplicate_username()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
