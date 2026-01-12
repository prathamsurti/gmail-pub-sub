import requests
import json

def test_analyze():
    url = "http://localhost:8001/analyze"
    
    payload = {
        "email_sender": "potential-client@example.com",
        "email_subject": "Inquiry about Enterprise Pricing",
        "email_body": "Hi, we are interested in your enterprise plan for 500 users. Can you send pricing?",
        "email_id": "msg_123",
        "thread_id": "thread_123"
    }
    
    try:
        print(f"📡 Sending request to {url}...")
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        if response.status_code == 200:
            print("Response Body:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_analyze()
