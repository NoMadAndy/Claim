#!/usr/bin/env python3
"""Test login endpoint to debug the issue"""
import requests
import json

API_BASE = "https://claim.macherwerkstatt.cc/api"

# Test existing user login
test_username = "testuser"
test_password = "TestPassword123!"

try:
    response = requests.post(
        f"{API_BASE}/auth/token",
        data={
            "username": test_username,
            "password": test_password
        },
        verify=False,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Response Text: {response.text}")
    
    if response.ok:
        data = response.json()
        print(f"\nLogin successful!")
        print(f"Token: {data.get('access_token', 'NO TOKEN')[:50]}...")
    else:
        print(f"\nLogin failed with status {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")
