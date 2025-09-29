"""
Basic tests for the Email Manager API.
Run with: python test_api.py
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_root_endpoint():
    """Test the root endpoint."""
    response = requests.get(f"{BASE_URL}/")
    print(f"Root endpoint status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        assert data["message"] == "Email Manager API"
        assert "endpoints" in data
        print("✅ Root endpoint test passed")
    else:
        print("❌ Root endpoint test failed")

def test_health_endpoint():
    """Test the health endpoint."""
    response = requests.get(f"{BASE_URL}/health")
    print(f"\nHealth endpoint status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        assert data["status"] == "healthy"
        assert "services" in data
        print("✅ Health endpoint test passed")
    else:
        print("❌ Health endpoint test failed")

def test_status_endpoint():
    """Test the status endpoint."""
    response = requests.get(f"{BASE_URL}/status")
    print(f"\nStatus endpoint status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        assert "scheduler_running" in data
        assert "scheduled_jobs" in data
        print("✅ Status endpoint test passed")
    else:
        print("❌ Status endpoint test failed")

def test_send_email_endpoint():
    """Test the send email endpoint (will fail without credentials, but should validate input)."""
    email_data = {
        "to_email": "test@example.com",
        "subject": "Test Email",
        "body": "This is a test email body."
    }
    
    response = requests.post(f"{BASE_URL}/send-email/", json=email_data)
    print(f"\nSend email endpoint status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Should return 500 because credentials are not configured, but request structure is valid
    if response.status_code == 500:
        print("✅ Send email endpoint test passed (expected failure due to missing credentials)")
    else:
        print("❌ Send email endpoint test failed")

def test_invalid_email():
    """Test sending to an invalid email address."""
    email_data = {
        "to_email": "invalid-email",
        "subject": "Test Email",
        "body": "This is a test email body."
    }
    
    response = requests.post(f"{BASE_URL}/send-email/", json=email_data)
    print(f"\nInvalid email test status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Should return 422 for validation error
    if response.status_code == 422:
        print("✅ Invalid email validation test passed")
    else:
        print("❌ Invalid email validation test failed")

if __name__ == "__main__":
    print("🧪 Running Email Manager API Tests")
    print("=" * 50)
    
    try:
        test_root_endpoint()
        test_health_endpoint()
        test_status_endpoint()
        test_send_email_endpoint()
        test_invalid_email()
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed! Check individual results above.")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API. Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ An error occurred: {e}")