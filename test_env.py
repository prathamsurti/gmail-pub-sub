"""
Test script to verify .env loading and API key
"""
import os
from dotenv import load_dotenv
from pathlib import Path

print("=" * 60)
print("🔍 ENVIRONMENT VARIABLE CHECK")
print("=" * 60)

# Try loading from different locations
locations = [
    ".env",
    "backend/.env",
    "../backend/.env"
]

for loc in locations:
    if os.path.exists(loc):
        print(f"\n✅ Found .env at: {loc}")
        load_dotenv(loc)
        break
else:
    print("\n⚠️  No .env file found, checking system environment")
    load_dotenv()

# Check key variables
api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OPENROUTER_MODEL")
temp = os.getenv("LLM_TEMPERATURE")

print("\n" + "=" * 60)
print("📊 LOADED CONFIGURATION")
print("=" * 60)

if api_key:
    masked_key = f"{api_key[:15]}...{api_key[-10:]}" if len(api_key) > 25 else "***"
    print(f"✅ OPENROUTER_API_KEY: {masked_key}")
else:
    print("❌ OPENROUTER_API_KEY: NOT FOUND")

print(f"✅ OPENROUTER_MODEL: {model or 'NOT SET (will use default)'}")
print(f"✅ LLM_TEMPERATURE: {temp or 'NOT SET (will use default)'}")

print("\n" + "=" * 60)
print("🧪 TESTING OPENROUTER CONNECTION")
print("=" * 60)

if api_key:
    import requests
    
    # Test with a simple, free model that works
    test_model = "google/gemini-2.0-flash-exp:free"
    
    print(f"\n🤖 Testing model: {test_model}")
    print("📡 Sending test request to OpenRouter...")
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://github.com/your-repo",
                "X-Title": "Gmail Agent Test",
                "Content-Type": "application/json"
            },
            json={
                "model": test_model,
                "messages": [
                    {"role": "user", "content": "Say 'test successful' if you can read this."}
                ],
                "max_tokens": 10
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ SUCCESS! API key is valid")
            print(f"   Response: {response.json()['choices'][0]['message']['content']}")
        else:
            print(f"❌ FAILED with status {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
else:
    print("❌ Cannot test - API key not found")

print("\n" + "=" * 60)
