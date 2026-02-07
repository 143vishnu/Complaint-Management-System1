import requests
import json

BASE_URL = "http://localhost:6969/api/auth"

def test_login(email, password):
    print(f"\nTesting login for: {email}")
    try:
        response = requests.post(
            f"{BASE_URL}/login",
            json={"email": email, "password": password}
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        if data.get('success'):
            print(f"Success! Message: {data.get('message')}")
            user = data.get('data', {}).get('user', {})
            print(f"User Role: {user.get('role')}")
            if user.get('role') == 'admin':
                print("PASSED: Role is admin (Should redirect to /admin-dashboard)")
            else:
                print(f"PASSED: Role is {user.get('role')} (Should redirect to /dashboard)")
            return data.get('data', {}).get('token')
        else:
            print(f"FAILED: {data.get('message')}")
    except Exception as e:
        print(f"ERROR: {e}")
    return None

def test_get_all_complaints(token):
    print("\nTesting retrieval of all complaints (Admin Only)")
    try:
        response = requests.get(
            "http://localhost:6969/api/complaints/all",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        if data.get('success'):
            complaints = data.get('data', {}).get('complaints', [])
            print(f"PASSED: Found {len(complaints)} complaints")
        else:
            print(f"FAILED: {data.get('message')}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    # Test Student Login
    test_login("student@example.com", "student123")
    
    # Test Faculty Login
    test_login("faculty@example.com", "faculty123")
    
    # Test Admin Login
    admin_token = test_login("admin@example.com", "admin123")
    
    if admin_token:
        test_get_all_complaints(admin_token)
