from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import json
import urllib.parse
from typing import Optional
import secrets
import asyncio
from collections import defaultdict
import threading
import time
from google.cloud import pubsub_v1
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Gmail Integration API")

# CORS middleware to allow frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://pn23g74h-3000.inc1.devtunnels.ms",
        "*"  # Allow all origins
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (frontend)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..")
if os.path.exists(os.path.join(STATIC_DIR, "index.html")):
    @app.get("/app", response_class=HTMLResponse)
    @app.get("/app/", response_class=HTMLResponse)
    async def serve_frontend():
        """Serve the frontend application"""
        index_path = os.path.join(STATIC_DIR, "index.html")
        with open(index_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())

# Load credentials from jaano-gmail.json file
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "..", "jaano-gmail.json")

try:
    with open(CREDENTIALS_FILE, 'r') as f:
        creds_data = json.load(f)
        if "installed" in creds_data:
            client_config = creds_data["installed"]
            GOOGLE_CLIENT_ID = client_config["client_id"]
            GOOGLE_CLIENT_SECRET = client_config["client_secret"]
        elif "web" in creds_data:
            client_config = creds_data["web"]
            GOOGLE_CLIENT_ID = client_config["client_id"]
            GOOGLE_CLIENT_SECRET = client_config["client_secret"]
        else:
            raise ValueError("Invalid credentials file format")
except FileNotFoundError:
    # Fallback to environment variables
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "YOUR_GOOGLE_CLIENT_SECRET")
    print("Warning: jaano-gmail.json not found, using environment variables")

REDIRECT_URI = "http://localhost:8000/auth/callback"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# OAuth scopes for Gmail access
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]

# In-memory storage (use database in production)
sessions = {}
SESSIONS_FILE = Path(__file__).parent / "sessions-cache.json"


def load_sessions_from_disk():
    """Load sessions from disk if cache file exists"""
    global sessions
    if SESSIONS_FILE.exists():
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                sessions = json.load(f)
            print(f"💾 Loaded {len(sessions)} sessions from disk")
        except Exception as e:
            print(f"⚠️ Could not load sessions cache: {e}")


def save_sessions_to_disk():
    """Persist sessions to disk (best-effort)"""
    try:
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f)
    except Exception as e:
        print(f"⚠️ Could not save sessions cache: {e}")


# Load any cached sessions at startup (module import time)
load_sessions_from_disk()

# SSE connections for real-time notifications
sse_connections = defaultdict(list)  # session_id -> list of queues

# Helper function to refresh credentials
def refresh_session_credentials(session_id: str):
    """Refresh access token for a session"""
    session = sessions.get(session_id)
    if not session or not session.get("refresh_token"):
        return None
    
    try:
        credentials = Credentials(
            token=session["access_token"],
            refresh_token=session["refresh_token"],
            token_uri=session["token_uri"],
            client_id=session["client_id"],
            client_secret=session["client_secret"],
            scopes=session["scopes"]
        )
        
        # Refresh the token
        import google.auth.transport.requests
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        
        # Update session with new token
        sessions[session_id]["access_token"] = credentials.token
        sessions[session_id]["token_refreshed"] = True  # Flag for frontend
        save_sessions_to_disk()
        
        print(f"✅ Refreshed token for session: {session_id[:20]}...")
        return credentials
        
    except Exception as e:
        print(f"❌ Token refresh failed: {e}")
        return None

# Helper function to get valid credentials
def get_valid_credentials(session_id: str):
    """Get credentials, refreshing if necessary"""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session. Please login again.")
    
    credentials = Credentials(
        token=session["access_token"],
        refresh_token=session["refresh_token"],
        token_uri=session["token_uri"],
        client_id=session["client_id"],
        client_secret=session["client_secret"],
        scopes=session["scopes"]
    )
    
    # Check if token is expired and refresh if needed
    if credentials.expired and credentials.refresh_token:
        print(f"🔄 Token expired, refreshing...")
        refreshed = refresh_session_credentials(session_id)
        if refreshed:
            credentials = refreshed
        else:
            raise HTTPException(status_code=401, detail="Failed to refresh token. Please login again.")
    
    return credentials, session.get("token_refreshed", False)  # Return refresh flag

# Pydantic models
class TokenRequest(BaseModel):
    code: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str]
    user_info: dict
    session_id: str

class SyncRequest(BaseModel):
    session_id: str
    max_results: int = 10
    unread_only: bool = True  # Filter for unread emails only

class WatchRequest(BaseModel):
    session_id: str
    topic_name: str  # Format: projects/{project-id}/topics/{topic-name}

@app.get("/")
async def root():
    """API root - returns info or redirects to frontend"""
    # If accessed from browser, redirect to frontend
    return {
        "message": "Gmail Integration API",
        "status": "running",
        "frontend_url": FRONTEND_URL,
        "app_url": f"{REDIRECT_URI.replace('/auth/callback', '')}/app",
        "endpoints": {
            "app": "/app (Frontend UI)",
            "auth": "/auth/login",
            "docs": "/docs",
            "health": "/health"
        },
        "tip": "Visit /app to access the frontend interface"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "frontend_url": FRONTEND_URL,
        "backend_url": REDIRECT_URI.replace("/auth/callback", ""),
        "active_sessions": len(sessions)
    }

@app.get("/auth/login")
async def login():
    """Initiate Google OAuth flow"""
    try:
        # Create client config for OAuth flow
        client_config = {
            "installed": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return {
            "authorization_url": authorization_url,
            "state": state
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate OAuth: {str(e)}")

@app.get("/auth/callback")
async def auth_callback(code: str, state: str):
    """Handle OAuth callback from Google"""
    try:
        client_config = {
            "installed": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
            state=state
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get user info
        user_info = get_user_info(credentials)
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        sessions[session_id] = {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "user_info": user_info
        }
        save_sessions_to_disk()
        save_sessions_to_disk()
        
        # Redirect back to frontend with session data
        frontend_url = f"{FRONTEND_URL}/?session_id={session_id}&access_token={credentials.token}&user_name={urllib.parse.quote(user_info['name'])}&user_email={urllib.parse.quote(user_info['email'])}"
        if credentials.refresh_token:
            frontend_url += f"&refresh_token={credentials.refresh_token}"
        
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        # Redirect to frontend with error
        return RedirectResponse(url=f"{FRONTEND_URL}/?error=auth_failed")

@app.post("/auth/token")
async def exchange_token(token_request: TokenRequest):
    """Exchange authorization code for tokens"""
    try:
        client_config = {
            "installed": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        flow.fetch_token(code=token_request.code)
        credentials = flow.credentials
# [MermaidChart: e2be3b28-9ab4-4645-aa17-d7dad0b8d118]
# [MermaidChart: e2be3b28-9ab4-4645-aa17-d7dad0b8d118]
# [MermaidChart: a34e1753-3d8a-44a9-8a1f-f3a22fb3ed4f]
# [MermaidChart: a34e1753-3d8a-44a9-8a1f-f3a22fb3ed4f]
# [MermaidChart: a34e1753-3d8a-44a9-8a1f-f3a22fb3ed4f]
        
        # Get user info
        user_info = get_user_info(credentials)
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        sessions[session_id] = {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "user_info": user_info
        }
        
        return TokenResponse(
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            user_info=user_info,
            session_id=session_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")

@app.get("/gmail/sync")
async def sync_gmail(session_id: str, max_results: int = 10, unread_only: bool = True):
    """Sync Gmail messages for authenticated user"""
    try:
        # Get valid credentials (auto-refreshes if expired)
        credentials, token_refreshed = get_valid_credentials(session_id)
        session = sessions.get(session_id)
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=credentials)
        
        # Fetch messages (unread only if requested)
        query_params = {
            'userId': 'me',
            'maxResults': max_results
        }
        
        if unread_only:
            query_params['q'] = 'is:unread'
        
        results = service.users().messages().list(**query_params).execute()
        
        messages = results.get('messages', [])
        
        # Get full message details
        detailed_messages = []
        for msg in messages[:max_results]:
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'To', 'Subject', 'Date']
            ).execute()
            
            # Extract headers
            headers = {}
            for header in message.get('payload', {}).get('headers', []):
                name = header['name']
                if name in ['From', 'To', 'Subject', 'Date']:
                    headers[name] = header['value']
            
            # Convert internalDate to ISO format
            internal_date_ms = int(message.get('internalDate', 0))
            from datetime import datetime
            date_iso = datetime.fromtimestamp(internal_date_ms / 1000).isoformat() if internal_date_ms else None
            
            detailed_messages.append({
                "id": message['id'],
                "threadId": message['threadId'],
                "snippet": message.get('snippet', ''),
                "from": headers.get('From', 'Unknown'),
                "to": headers.get('To', ''),
                "subject": headers.get('Subject', '(No subject)'),
                "date": date_iso or headers.get('Date', ''),
                "internalDate": message.get('internalDate'),
                "labelIds": message.get('labelIds', []),
                "isUnread": 'UNREAD' in message.get('labelIds', [])
            })
        
        result = {
            "success": True,
            "message_count": len(detailed_messages),
            "messages": detailed_messages,
            "user_email": session["user_info"]["email"]
        }
        
        # Include new access token if it was refreshed
        if token_refreshed:
            result["new_access_token"] = session["access_token"]
            sessions[session_id]["token_refreshed"] = False  # Reset flag
        
        return result
        
    except HttpError as error:
        if error.resp.status == 401:
            raise HTTPException(status_code=401, detail="Token expired. Please login again.")
        raise HTTPException(status_code=500, detail=f"Gmail API error: {str(error)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@app.post("/gmail/refresh-token")
async def refresh_token(session_id: str):
    """Refresh access token using refresh token"""
    try:
        session = sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        credentials = Credentials(
            token=session["access_token"],
            refresh_token=session["refresh_token"],
            token_uri=session["token_uri"],
            client_id=session["client_id"],
            client_secret=session["client_secret"],
            scopes=session["scopes"]
        )
        
        # Refresh token
        credentials.refresh(Request())
        
        # Update session
        sessions[session_id]["access_token"] = credentials.token
        save_sessions_to_disk()
        
        return {
            "success": True,
            "access_token": credentials.token
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")

@app.post("/auth/logout")
async def logout(session_id: str):
    """Logout user and clear session"""
    if session_id in sessions:
        del sessions[session_id]
        save_sessions_to_disk()
    return {"success": True, "message": "Logged out successfully"}

@app.get("/user/info")
async def get_user_info_endpoint(session_id: str):
    """Get current user info"""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    return {
        "user_info": session["user_info"]
    }

@app.post("/gmail/watch")
async def watch_gmail(watch_request: WatchRequest):
    """Set up Gmail push notifications using Pub/Sub"""
    try:
        print(f"📡 Watch request received: {watch_request}")
        
        # Get valid credentials (auto-refreshes if expired)
        credentials, token_refreshed = get_valid_credentials(watch_request.session_id)
        
        service = build('gmail', 'v1', credentials=credentials)
        
        # Set up watch request
        request_body = {
            'topicName': watch_request.topic_name,
            'labelIds': ['INBOX', 'UNREAD']  # Watch for unread inbox messages
        }
        
        print(f"🔔 Setting up Gmail watch with topic: {watch_request.topic_name}")
        
        watch_response = service.users().watch(
            userId='me',
            body=request_body
        ).execute()
        
        print(f"✅ Gmail watch activated: historyId={watch_response.get('historyId')}")
        
        # Store watch info in session
        sessions[watch_request.session_id]['watch'] = {
            'historyId': watch_response['historyId'],
            'expiration': watch_response['expiration']
        }
        save_sessions_to_disk()
        
        return {
            "success": True,
            "historyId": watch_response['historyId'],
            "expiration": watch_response['expiration'],
            "message": "Gmail watch set up successfully"
        }
        
    except HttpError as error:
        error_details = error.content.decode() if error.content else str(error)
        print(f"❌ Gmail API error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Gmail API error: {error_details}")
    except Exception as e:
        print(f"❌ Watch setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Watch setup failed: {str(e)}")

@app.post("/gmail/webhook")
async def gmail_webhook(request: Request):
    """Webhook to receive Gmail push notifications"""
    try:
        # Get the notification data
        notification = await request.json()
        
        # Extract message data from Pub/Sub
        message = notification.get('message', {})
        data = message.get('data', '')
        
        # Decode base64 data
        import base64
        if data:
            decoded_data = base64.b64decode(data).decode('utf-8')
            email_data = json.loads(decoded_data)
            
            # Log the notification
            print(f"📧 New email notification: {email_data}")
            
            # Notify all connected SSE clients
            for session_id, queues in sse_connections.items():
                for queue in queues:
                    await queue.put({"type": "new_email", "data": email_data})
            
            return {"success": True, "message": "Notification received"}
        
        return {"success": True, "message": "Empty notification"}
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return {"success": False, "error": str(e)}

@app.get("/events")
async def sse_endpoint(session_id: str):
    """Server-Sent Events endpoint for real-time notifications"""
    async def event_generator():
        queue = asyncio.Queue()
        sse_connections[session_id].append(queue)
        
        try:
            while True:
                # Wait for new events
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            sse_connections[session_id].remove(queue)
            raise
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.post("/notify-new-email")
async def notify_new_email(request: Request):
    """Receive notification from listener.py and broadcast to SSE clients"""
    try:
        data = await request.json()
        print(f"📧 Pub/Sub notification: {data}")
        
        # Broadcast to all connected SSE clients
        notification_count = 0
        for session_id, queues in sse_connections.items():
            for queue in queues:
                await queue.put({"type": "new_email", "data": data})
                notification_count += 1
        
        print(f"✅ Broadcasted to {notification_count} SSE clients")
        return {"success": True, "notified_clients": notification_count}
        
    except Exception as e:
        print(f"❌ Notification error: {str(e)}")
        return {"success": False, "error": str(e)}

@app.post("/test-notification")
async def test_notification():
    """Test endpoint to manually trigger a notification"""
    try:
        notification_count = 0
        for session_id, queues in sse_connections.items():
            for queue in queues:
                await queue.put({
                    "type": "new_email",
                    "data": {
                        "test": True,
                        "message": "Test notification from backend"
                    }
                })
                notification_count += 1
        
        print(f"🧪 Test notification sent to {notification_count} clients")
        return {
            "success": True,
            "message": "Test notification sent",
            "clients_notified": notification_count
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

class MarkReadRequest(BaseModel):
    session_id: str
    message_id: str

@app.post("/gmail/mark-read")
async def mark_as_read(mark_request: MarkReadRequest):
    """Mark a Gmail message as read"""
    try:
        # Get valid credentials (auto-refreshes if expired)
        credentials, token_refreshed = get_valid_credentials(mark_request.session_id)
        
        service = build('gmail', 'v1', credentials=credentials)
        
        # Remove UNREAD label
        service.users().messages().modify(
            userId='me',
            id=mark_request.message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        
        print(f"✅ Message {mark_request.message_id} marked as read")
        
        return {
            "success": True,
            "message": "Message marked as read"
        }
        
    except HttpError as error:
        raise HTTPException(status_code=500, detail=f"Gmail API error: {str(error)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mark read failed: {str(e)}")

@app.get("/gmail/unread-count")
async def get_unread_count(session_id: str):
    """Get count of unread emails"""
    try:
        # Get valid credentials (auto-refreshes if expired)
        credentials, token_refreshed = get_valid_credentials(session_id)
        
        service = build('gmail', 'v1', credentials=credentials)
        
        # Get label info which includes message counts
        label = service.users().labels().get(
            userId='me',
            id='INBOX'
        ).execute()
        
        return {
            "success": True,
            "count": label.get('messagesUnread', 0),
            "unread_count": label.get('messagesUnread', 0),
            "total_count": label.get('messagesTotal', 0)
        }
        
    except HttpError as error:
        raise HTTPException(status_code=500, detail=f"Gmail API error: {str(error)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get count: {str(e)}")

class SendReplyRequest(BaseModel):
    session_id: str
    to: str
    subject: str
    message: str
    thread_id: Optional[str] = None
    in_reply_to_message_id: Optional[str] = None

@app.post("/gmail/send-reply")
async def send_reply(reply_request: SendReplyRequest):
    """Send a reply to an email"""
    try:
        # Get valid credentials (auto-refreshes if expired)
        credentials, token_refreshed = get_valid_credentials(reply_request.session_id)
        
        service = build('gmail', 'v1', credentials=credentials)
        
        # Extract email address from "Name <email@domain.com>" format
        import re
        to_email = reply_request.to
        email_match = re.search(r'<(.+?)>', to_email)
        if email_match:
            to_email = email_match.group(1)
        
        # Create the email message
        from email.mime.text import MIMEText
        import base64
        
        message = MIMEText(reply_request.message)
        message['to'] = to_email
        message['subject'] = reply_request.subject
        
        # Add In-Reply-To and References headers for threading
        if reply_request.in_reply_to_message_id:
            # Get the original message to extract Message-ID header
            try:
                original_msg = service.users().messages().get(
                    userId='me',
                    id=reply_request.in_reply_to_message_id,
                    format='metadata',
                    metadataHeaders=['Message-ID']
                ).execute()
                
                for header in original_msg.get('payload', {}).get('headers', []):
                    if header['name'] == 'Message-ID':
                        message['In-Reply-To'] = header['value']
                        message['References'] = header['value']
                        break
            except:
                pass  # Continue even if we can't get the original message ID
        
        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send the message
        send_body = {'raw': raw_message}
        if reply_request.thread_id:
            send_body['threadId'] = reply_request.thread_id
        
        sent_message = service.users().messages().send(
            userId='me',
            body=send_body
        ).execute()
        
        print(f"✅ Reply sent: {sent_message['id']}")
        
        return {
            "success": True,
            "message_id": sent_message['id'],
            "thread_id": sent_message.get('threadId')
        }
        
    except HttpError as error:
        print(f"❌ Gmail API error: {error}")
        raise HTTPException(status_code=500, detail=f"Gmail API error: {str(error)}")
    except Exception as e:
        print(f"❌ Send reply failed: {e}")
        raise HTTPException(status_code=500, detail=f"Send reply failed: {str(e)}")

def get_user_info(credentials):
    """Fetch user information from Google"""
    try:
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        return {
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "verified_email": user_info.get("verified_email")
        }
    except Exception as e:
        return {
            "email": "unknown",
            "name": "Unknown User",
            "picture": "",
            "verified_email": False
        }

# Pub/Sub Listener Background Task
def pubsub_listener():
    """Background thread to listen for Pub/Sub messages"""
    project_id = "jaano-gmail"
    subscription_id = "gmail-pull-sub"
    
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)
    
    print(f"\n🎧 Pub/Sub Listener started: {subscription_path}")
    
    def process_messages():
        """Pull and process messages"""
        try:
            response = subscriber.pull(
                request={"subscription": subscription_path, "max_messages": 10},
                timeout=30
            )
            
            if response.received_messages:
                print(f"\n📬 Received {len(response.received_messages)} message(s)")
                
                ack_ids = []
                for received_message in response.received_messages:
                    message = received_message.message
                    
                    print(f"\n📧 New Email Notification")
                    print(f"   Message ID: {message.message_id}")
                    print(f"   Attributes: {dict(message.attributes)}")
                    
                    # Extract email information
                    email_address = message.attributes.get('emailAddress', 'unknown')
                    history_id = message.attributes.get('historyId', 'unknown')
                    
                    # Broadcast to SSE clients (sync version)
                    notification_data = {
                        "email_address": email_address,
                        "history_id": history_id,
                        "message_id": message.message_id,
                        "publish_time": str(message.publish_time)
                    }
                    
                    # Send to all SSE connections without async
                    notification_count = 0
                    for session_id, queues in sse_connections.items():
                        for queue in queues:
                            try:
                                queue.put_nowait({"type": "new_email", "data": notification_data})
                                notification_count += 1
                            except:
                                pass
                    
                    if notification_count > 0:
                        print(f"   ✅ Broadcasted to {notification_count} SSE client(s)")
                    
                    ack_ids.append(received_message.ack_id)
                
                # Acknowledge all messages
                if ack_ids:
                    subscriber.acknowledge(
                        request={"subscription": subscription_path, "ack_ids": ack_ids}
                    )
                    print(f"✓ Acknowledged {len(ack_ids)} message(s)")
        
        except Exception as e:
            print(f"⚠️  Listener error: {e}")
    
    # Main polling loop
    while True:
        try:
            process_messages()
        except Exception as e:
            print(f"❌ Polling error: {e}")
        time.sleep(5)  # Poll every 5 seconds

async def broadcast_notification(data):
    """Broadcast notification to all SSE clients"""
    notification_count = 0
    for session_id, queues in sse_connections.items():
        for queue in queues:
            await queue.put({"type": "new_email", "data": data})
            notification_count += 1
    
    if notification_count > 0:
        print(f"   ✅ Broadcasted to {notification_count} SSE client(s)")

@app.on_event("startup")
async def startup_event():
    """Start background tasks on app startup"""
    # Check if service account credentials are set
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        # Start Pub/Sub listener in background thread
        listener_thread = threading.Thread(target=pubsub_listener, daemon=True)
        listener_thread.start()
        print("✅ FastAPI started with integrated Pub/Sub listener")
    else:
        print("⚠️  GOOGLE_APPLICATION_CREDENTIALS not set - Pub/Sub listener disabled")
        print("   Set: $env:GOOGLE_APPLICATION_CREDENTIALS='path/to/service-account-key.json'")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)