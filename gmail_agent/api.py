from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .graph import agent_graph
import uvicorn
import os


app = FastAPI(title="Gmail Agent Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "*"  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EmailRequest(BaseModel):
    email_sender: str
    email_subject: str
    email_body: str
    email_id: str
    thread_id: str

@app.get("/")
def read_root():
    return {"status": "Agent Service Running"}

@app.post("/analyze")
async def analyze_email(request: EmailRequest):
    try:
        print("\n" + "#"*60)
        print("🚀 NEW EMAIL ANALYSIS REQUEST")
        print("#"*60)
        print(f"📨 From: {request.email_sender}")
        print(f"📋 Subject: {request.email_subject}")
        print(f"📝 Body length: {len(request.email_body)} characters")
        print(f"🆔 Email ID: {request.email_id}")
        print(f"🧵 Thread ID: {request.thread_id}")
        print("#"*60 + "\n")
        
        # Initial State
        initial_state = {
            "email_sender": request.email_sender,
            "email_subject": request.email_subject,
            "email_body": request.email_body,
            "email_id": request.email_id,
            "thread_id": request.thread_id
        }
        
        print("🔄 Starting LangGraph agent pipeline...\n")
        # Run Graph
        result = agent_graph.invoke(initial_state)
        
        response_data = {
            "success": True,
            "action": result.get("final_action"),
            "draft": result.get("email_draft"),
            "draft_type": result.get("draft_type", "unknown"),  # hot_auto, warm_review, cold_template
            "final_action": result.get("final_action"),  # Alias for backend compatibility
            "analysis": {
                "is_lead": result.get("is_lead"),
                "classification": result.get("classification"),
                "confidence": result.get("confidence_score"),
                "reasoning": result.get("reasoning")
            }
        }
        
        print("\n" + "#"*60)
        print("✅ PIPELINE COMPLETE - FINAL SUMMARY")
        print("#"*60)
        print(f"Is Lead: {result.get('is_lead')}")
        print(f"Classification: {result.get('classification')}")
        print(f"Action: {result.get('final_action')}")
        print(f"Draft Ready: {bool(result.get('email_draft'))}")
        print("#"*60 + "\n")
        
        return response_data
        
    except Exception as e:
        print("\n" + "#"*60)
        print(f"❌ FATAL ERROR IN PIPELINE")
        print("#"*60)
        print(f"Error: {str(e)}")
        print(f"Type: {type(e).__name__}")
        print("#"*60 + "\n")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
