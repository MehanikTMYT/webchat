#!/usr/bin/env python3
"""
Test script to verify the API endpoints are working correctly
"""
import requests
import json
import time

# Base URL of the running API
BASE_URL = "http://localhost:8000"

def test_api_endpoints():
    print("Testing API endpoints...")
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health endpoint error: {e}")
    
    # Test root endpoint
    print("\n2. Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Root endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Root endpoint error: {e}")
    
    # Test network config endpoint
    print("\n3. Testing network config endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/network/config")
        print(f"Network config endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Network config endpoint error: {e}")
    
    # Test registration endpoint
    print("\n4. Testing registration endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json={
            "username": "testuser",
            "password": "testpass"
        })
        print(f"Registration endpoint: {response.status_code}")
        if response.status_code == 200:
            token_data = response.json()
            print(f"Registration successful, token received")
            auth_token = token_data.get("access_token")
        else:
            print(f"Registration response: {response.text}")
    except Exception as e:
        print(f"Registration endpoint error: {e}")
        auth_token = None
    
    if auth_token:
        # Test token verification
        print("\n5. Testing token verification...")
        try:
            headers = {"Authorization": f"Bearer {auth_token}"}
            response = requests.get(f"{BASE_URL}/auth/verify", headers=headers)
            print(f"Token verification: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"Token verification error: {e}")
        
        # Test creating a session
        print("\n6. Testing session creation...")
        try:
            headers = {"Authorization": f"Bearer {auth_token}"}
            response = requests.post(f"{BASE_URL}/api/sessions", json={
                "title": "Test Session"
            }, headers=headers)
            print(f"Session creation: {response.status_code}")
            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data.get("id")
                print(f"Session created with ID: {session_id}")
            else:
                print(f"Session creation response: {response.text}")
        except Exception as e:
            print(f"Session creation error: {e}")
            session_id = None
        
        if session_id:
            # Test getting sessions
            print("\n7. Testing get sessions...")
            try:
                headers = {"Authorization": f"Bearer {auth_token}"}
                response = requests.get(f"{BASE_URL}/api/sessions", headers=headers)
                print(f"Get sessions: {response.status_code} - {len(response.json())} sessions")
            except Exception as e:
                print(f"Get sessions error: {e}")
            
            # Test sending a message
            print("\n8. Testing send message...")
            try:
                headers = {"Authorization": f"Bearer {auth_token}"}
                response = requests.post(f"{BASE_URL}/api/chat/send", json={
                    "session_id": session_id,
                    "message": "Hello, how are you?"
                }, headers=headers)
                print(f"Send message: {response.status_code}")
                if response.status_code == 200:
                    response_data = response.json()
                    print(f"Bot response: {response_data.get('response', 'No response')}")
            except Exception as e:
                print(f"Send message error: {e}")
            
            # Test getting messages
            print("\n9. Testing get messages...")
            try:
                headers = {"Authorization": f"Bearer {auth_token}"}
                response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/messages", headers=headers)
                print(f"Get messages: {response.status_code} - {len(response.json())} messages")
            except Exception as e:
                print(f"Get messages error: {e}")

if __name__ == "__main__":
    print("Waiting for server to be ready...")
    time.sleep(2)  # Wait a bit for server to be fully ready
    test_api_endpoints()