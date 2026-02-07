import requests
import json

BASE_URL = "http://localhost:6969"

def test_enhanced_features():
    print("--- Testing Enhanced Features ---")
    
    # 1. Login as Admin
    print("Logging in as Admin...")
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"FAILED to login: {response.text}")
        return
    
    token_data = response.json().get('data')
    token = token_data.get('token') if token_data else None
    print(f"Token: {token}")
    headers = {"Authorization": f"Bearer {token}"}
    print("SUCCESS: Admin logged in.")

    # 2. Check Enhanced Stats (Sentiment)
    print("Fetching Enhanced Stats...")
    stats_res = requests.get(f"{BASE_URL}/api/complaints/stats", headers=headers)
    if stats_res.status_code == 200:
        data = stats_res.json().get('data')
        print(f"Stats Data: {json.dumps(data, indent=2)}")
        if 'sentiment_stats' in data:
            print("✅ VERIFIED: Sentiment stats present.")
        else:
            print("❌ FAILED: Sentiment stats missing.")
    else:
        print(f"FAILED to fetch stats ({stats_res.status_code}): {stats_res.text}")

    # 3. Test ML Predict (Classify)
    print("Testing ML Classify endpoint...")
    ml_data = {"query": "I am very frustrated that my internet is not working in the hostel!"}
    ml_res = requests.post(f"{BASE_URL}/api/ml/classify", headers=headers, json=ml_data)
    if ml_res.status_code == 200:
        ml_result = ml_res.json().get('data')
        print(f"ML Result: {json.dumps(ml_result, indent=2)}")
        if 'sentiment' in ml_result and 'confidence' in ml_result:
            print("✅ VERIFIED: ML response includes sentiment and confidence.")
        else:
            print("❌ FAILED: ML response missing advanced data.")
    else:
        print(f"FAILED to test ML: {ml_res.text}")

    # 4. Test AI Chatbot Suggestions
    print("Testing AI Chatbot Suggestions...")
    chat_data = {"message": "How do I track my complaint?"}
    chat_res = requests.post(f"{BASE_URL}/api/chatbot/chat", headers=headers, json=chat_data)
    if chat_res.status_code == 200:
        chat_result = chat_res.json()
        print(f"Chat Suggestions: {chat_result.get('suggestions')}")
        if 'suggestions' in chat_result and len(chat_result['suggestions']) > 0:
            print("✅ VERIFIED: AI Assistant provides proactive suggestions.")
        else:
            print("❌ FAILED: AI Assistant missing suggestions.")
    else:
        print(f"FAILED to test Chatbot: {chat_res.text}")

if __name__ == "__main__":
    test_enhanced_features()
