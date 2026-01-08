import time
import httpx
from google.cloud import pubsub_v1

# Configuration
project_id = "jaano-gmail"
subscription_id = "gmail-pull-sub"
BACKEND_API = "http://localhost:8000"

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)

print(f"🎧 Polling for messages on {subscription_path}...")
print(f"📡 Backend API: {BACKEND_API}")
print(f"Press Ctrl+C to stop\n")

def process_messages():
    """Pull and process messages"""
    # Pull messages
    response = subscriber.pull(
        request={"subscription": subscription_path, "max_messages": 10},
        timeout=30
    )
    
    if response.received_messages:
        print(f"\n📬 Received {len(response.received_messages)} message(s)")
        
        ack_ids = []
        for received_message in response.received_messages:
            message = received_message.message
            
            print(f"\n📧 ========== NEW MESSAGE ==========")
            print(f"Message ID: {message.message_id}")
            print(f"Publish Time: {message.publish_time}")
            print(f"Data: {message.data}")
            print(f"Attributes: {dict(message.attributes)}")
            
            # Extract email information
            email_address = message.attributes.get('emailAddress', 'unknown')
            history_id = message.attributes.get('historyId', 'unknown')
            
            print(f"📬 Email Address: {email_address}")
            print(f"📜 History ID: {history_id}")
            
            # Notify backend
            try:
                print(f"🔄 Notifying backend...")
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
                print(f"✅ Backend response: {response.status_code}")
                if response.status_code == 200:
                    print(f"   {response.json()}")
            except Exception as e:
                print(f"❌ Failed to notify backend: {e}")
            
            print("=" * 40)
            ack_ids.append(received_message.ack_id)
        
        # Acknowledge all messages
        if ack_ids:
            subscriber.acknowledge(
                request={"subscription": subscription_path, "ack_ids": ack_ids}
            )
            print(f"\n✓ Acknowledged {len(ack_ids)} message(s)\n")

# Main loop
try:
    while True:
        try:
            process_messages()
        except Exception as e:
            print(f"⚠️  Error processing messages: {e}")
        time.sleep(5)  # Poll every 5 seconds
        
except KeyboardInterrupt:
    print("\n\n⏹️  Stopping listener...")
