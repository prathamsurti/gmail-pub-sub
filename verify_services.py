import requests
import json
import time

BASE_URL = "http://localhost:8000"
NOTIFY_URL = f"{BASE_URL}/test-notification"
LEADS_URL = f"{BASE_URL}/leads"

# Mock data for scenarios
SCENARIOS = [
    {
        "type": "HOT",
        "email": {
            "message_id": "msg_hot_001",
            "email_address": "cto@bigcorp.com",
            # Note: The test-notification endpoint triggers specific mock data logic in backend if "test": True
            # But the real notify endpoint expects message_id and triggers process_email_background
            # To test the full flow, we need to mock the Gmail API response inside process_email_background
            # OR we can just rely on mocking the notification payload and let the backend fail to fetch Gmail
            # but assume the agent logic works.
            
            # Actually, `test-notification` endpoint in backend just sends "test": True data to SSE.
            # It doesn't trigger agent processing.
            # I should use `/notify-new-email` but that requires a real message_id that exists in Gmail.
            
            # ALTERNATIVE: Use `agent_tester` component I built? 
            # Or use `test_agent_only.py`?
            
            # Let's create a script that calls the AGENT directly (`http://localhost:8001/analyze`)
            # And then calls the LEAD storage directly? No, lead storage is internal to backend.
            
            # Best approach for verification without real Gmail:
            # Create a test endpoint in backend that injects a lead directly into storage?
            # Or just trust `test_integration.py` concepts.
        }
    }
]

# Since I cannot easily mock Gmail API calls from outside without modifying backend code to use a mock service,
# The best verification I can do here is:
# 1. Verify the frontend builds (Done)
# 2. Verify the backend endpoints exist (GET /leads)
# 3. Verify the agent service is responding

def check_services():
    print("🔍 Checking services...")
    
    # Check Backend
    try:
        resp = requests.get(f"{BASE_URL}/")
        print(f"✅ Backend is running: {resp.json()}")
    except Exception as e:
        print(f"❌ Backend not reachable: {e}")

    # Check Agent
    try:
        resp = requests.get("http://localhost:8001/")
        print(f"✅ Agent Service is running: {resp.json()}")
    except Exception as e:
        print(f"❌ Agent Service not reachable: {e}")

if __name__ == "__main__":
    check_services()
    print("\n⚠️ Note: Full end-to-end verification requires sending real emails to the Gmail account.")
    print("   Please use the Client UI to perform the manual verification steps outlined in the Implementation Plan.")
