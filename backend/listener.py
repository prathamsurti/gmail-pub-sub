import os
import asyncio
import httpx
from google.cloud import pubsub_v1
from concurrent.futures import TimeoutError

# Project and subscription configuration
project_id = "jaano-gmail"
subscription_id = "gmail-pull-sub"

# Backend API to notify
BACKEND_API = "http://localhost:8000"

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)

def callback(message):
    """Handle incoming Pub/Sub messages"""
    print(f"\n📧 ========== NEW MESSAGE ==========")
    print(f"Message ID: {message.message_id}")
    print(f"Publish Time: {message.publish_time}")
    
    if message.data:
        print(f"Data: {message.data}")
    
    if message.attributes:
        print(f"Attributes: {message.attributes}")
        
        # Extract email information
        email_address = message.attributes.get('emailAddress', 'unknown')
        history_id = message.attributes.get('historyId', 'unknown')
        
        print(f"📬 Email Address: {email_address}")
        print(f"📜 History ID: {history_id}")
        
        # Notify all connected SSE clients via backend
        try:
            print(f"🔄 Notifying backend at {BACKEND_API}/notify-new-email...")
            response = httpx.post(
                f"{BACKEND_API}/notify-new-email",
                json={
                    "email_address": email_address,
                    "history_id": history_id,
                    "message_id": message.message_id,
                    "publish_time": str(message.publish_time)
                },
                timeout=5.0
            )
            print(f"✅ Backend response: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Failed to notify backend: {e}")
    else:
        print("⚠️  No attributes in message")
    
    # Acknowledge the message
    message.ack()
    print(f"✓ Message acknowledged")
    print("=" * 40 + "\n")

print(f"🎧 Listening for messages on {subscription_path}...\n")
print(f"📡 Backend API: {BACKEND_API}")
print(f"Press Ctrl+C to stop\n")

streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

# Keep the script running
with subscriber:
    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping listener...")
        streaming_pull_future.cancel()
        streaming_pull_future.result()
    except TimeoutError:
        streaming_pull_future.cancel()
        streaming_pull_future.result()
