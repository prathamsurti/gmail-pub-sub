"""
Quick test: Just the Agent Service (no Gmail integration)
"""
import requests
import json

def test_agent_with_lead():
    """Test with a clear business lead"""
    url = "http://localhost:8001/analyze"
    
    payload = {
        "email_sender": "cto@bigcorp.com",
        "email_subject": "Urgent: Enterprise Pricing for 1000 Users",
        "email_body": """Hi,
        
        We're looking to deploy your solution for our entire organization (1000+ users).
        We need this by end of month. Can you send pricing and schedule a call ASAP?

        Thanks,
        John Smith
        CTO, BigCorp Inc.
        """,
                "email_id": "test_msg_001",
                "thread_id": "test_thread_001"
            }
    
    print("=" * 60)
    print("🧪 TEST 1: Hot Lead (Enterprise Inquiry)")
    print("=" * 60)
    run_test(url, payload)


def test_agent_with_spam():
    """Test with obvious spam"""
    url = "http://localhost:8001/analyze"
    
    payload = {
        "email_sender": "noreply@marketing.com",
        "email_subject": "🎉 You've Won a Free iPhone!",
        "email_body": """Congratulations! You've been selected as a winner!
        
Click here to claim your FREE iPhone 15 Pro Max now!
Limited time offer. Act fast!
        """,
        "email_id": "test_msg_002",
        "thread_id": "test_thread_002"
    }
    
    print("\n" + "=" * 60)
    print("🧪 TEST 2: Spam/Marketing Email")
    print("=" * 60)
    run_test(url, payload)


def test_agent_with_warm_lead():
    """Test with a warm lead"""
    url = "http://localhost:8001/analyze"
    
    payload = {
        "email_sender": "startup@example.com",
        "email_subject": "Question about your product",
        "email_body": """Hi,
        
I came across your website and I'm interested in learning more about your product.
Could you send me some information?

Best regards,
Sarah
        """,
        "email_id": "test_msg_003",
        "thread_id": "test_thread_003"
    }
    
    print("\n" + "=" * 60)
    print("🧪 TEST 3: Warm Lead (General Inquiry)")
    print("=" * 60)
    run_test(url, payload)


def run_test(url, payload):
    """Execute the test"""
    try:
        print(f"\n📨 Testing email from: {payload['email_sender']}")
        print(f"📧 Subject: {payload['email_subject']}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ Agent Response:")
            print(f"   Is Lead: {result['analysis']['is_lead']}")
            print(f"   Classification: {result['analysis']['classification']}")
            print(f"   Confidence: {result['analysis']['confidence']}")
            print(f"   Action: {result['action']}")
            print(f"   Reasoning: {result['analysis']['reasoning']}")
            
            if result.get('draft'):
                print(f"\n📝 Draft Reply:")
                print(f"   To: {result['draft']['to']}")
                print(f"   Subject: {result['draft']['subject']}")
                print(f"   Body Preview: {result['draft']['body'][:200]}...")
        else:
            print(f"\n❌ Error {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Agent service not running!")
        print("   Start agent: cd gmail_agent && uvicorn api:app --port 8001")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")


if __name__ == "__main__":
    print("\n🤖 Testing Gmail Agent Service\n")
    print("Make sure agent service is running:")
    print("  cd gmail_agent && uvicorn api:app --port 8001\n")
    
    input("Press Enter to start tests...")
    
    test_agent_with_lead()
    test_agent_with_spam()
    test_agent_with_warm_lead()
    
    print("\n" + "=" * 60)
    print("✅ All tests complete!")
    print("=" * 60)
