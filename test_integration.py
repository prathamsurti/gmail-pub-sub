"""
Integration test: Simulate a Pub/Sub notification to trigger the full agent pipeline
"""
import requests
import json

def test_full_integration():
    """Test the complete flow: Pub/Sub → Backend → Agent → Gmail Action"""
    
    # This endpoint is what Pub/Sub calls when a new email arrives
    backend_url = "http://localhost:8000/notify-new-email"
    
    # Simulate what Pub/Sub sends
    # Note: For this to work, you need an actual email in your Gmail
    # You can get a real message_id by calling /gmail/sync first
    payload = {
        "email_address": "your-email@gmail.com",  # Replace with your Gmail
        "history_id": "12345",
        "message_id": "REPLACE_WITH_REAL_MESSAGE_ID",  # Get this from /gmail/sync
        "publish_time": "2026-01-12T10:00:00Z"
    }
    
    print("=" * 60)
    print("🧪 INTEGRATION TEST: Pub/Sub → Backend → Agent → Action")
    print("=" * 60)
    print(f"\n📡 Sending notification to: {backend_url}")
    print(f"📧 Email Address: {payload['email_address']}")
    print(f"📨 Message ID: {payload['message_id']}")
    print("\n⚠️  Note: You need to replace message_id with a real one from your Gmail\n")
    
    try:
        response = requests.post(backend_url, json=payload, timeout=5.0)
        
        print(f"\n✅ Response Status: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        print("\n" + "=" * 60)
        print("📝 What happens next (check backend logs):")
        print("  1. Backend fetches full email from Gmail API")
        print("  2. Backend calls Agent Service (localhost:8001)")
        print("  3. Strategist analyzes the email")
        print("  4. Executor drafts reply (if it's a lead)")
        print("  5. Backend sends reply via Gmail API")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Backend not running!")
        print("   Start backend: cd backend && uvicorn main:app --port 8000")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")


def get_real_message_id():
    """Helper: Get a real message ID from your Gmail inbox"""
    print("\n" + "=" * 60)
    print("📬 Fetching real message IDs from your Gmail...")
    print("=" * 60)
    
    session_id = input("\nEnter your session_id (from logging in): ").strip()
    
    if not session_id:
        print("❌ Session ID required. Login first via the frontend.")
        return
    
    sync_url = f"http://localhost:8000/gmail/sync?session_id={session_id}&max_results=5&unread_only=false"
    
    try:
        response = requests.get(sync_url, timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            messages = data.get("messages", [])
            
            if messages:
                print(f"\n✅ Found {len(messages)} emails:\n")
                for i, msg in enumerate(messages, 1):
                    print(f"{i}. ID: {msg['id']}")
                    print(f"   Subject: {msg['subject']}")
                    print(f"   From: {msg['from']}")
                    print(f"   Date: {msg['date']}\n")
                
                print("\nCopy one of these IDs and use it in the test above!")
            else:
                print("\n⚠️  No messages found in your inbox")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Backend not running!")
        print("   Start backend: cd backend && uvicorn main:app --port 8000")
    except Exception as e:
        print(f"\n❌ Failed: {e}")


if __name__ == "__main__":
    print("\n🧪 Gmail Agent Integration Test\n")
    print("Choose an option:")
    print("  1. Get real message IDs from Gmail")
    print("  2. Test full integration (requires message ID)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        get_real_message_id()
    elif choice == "2":
        test_full_integration()
    else:
        print("Invalid choice")
