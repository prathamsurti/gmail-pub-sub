import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from pathlib import Path

# Try to load .env from root or backend
if os.path.exists(".env"):
    load_dotenv(".env")
elif os.path.exists("backend/.env"):
    load_dotenv("backend/.env")
else:
    load_dotenv()

# Cold Lead Company Profile Template
COLD_LEAD_TEMPLATE = """
<p>Thank you for contacting us!</p>

<p>We appreciate your interest. Below are our company details:</p>

<h3>About Google</h3>
<p><strong>Google LLC</strong> is a global technology leader focused on improving the ways people connect with information.</p>

<p><strong>Our Services:</strong></p>
<ul>
    <li>Search Engine & Advertising Solutions</li>
    <li>Cloud Computing (Google Cloud Platform)</li>
    <li>Workspace & Productivity Tools (Gmail, Drive, Docs)</li>
    <li>Android & Mobile Solutions</li>
    <li>AI & Machine Learning Services</li>
</ul>

<p><strong>Contact Information:</strong></p>
<ul>
    <li>Website: <a href="https://www.google.com">www.google.com</a></li>
    <li>Headquarters: Mountain View, California, USA</li>
    <li>Founded: 1998</li>
</ul>

<p>If you have specific questions, please reply to this email and we'll be happy to assist.</p>

<p>Best regards,<br>
<strong>The Google Team</strong></p>
"""


class ExecutorOutput(BaseModel):
    action: str = Field(description="Action to take: 'send_reply', 'mark_read', or 'ignore'")
    subject: str = Field(description="Subject line for the reply email (must include 'Re:' prefix)")
    body: str = Field(description="Complete HTML-formatted email body with proper greeting, content, and signature. Must not be empty.")


def executor_node(state: dict):
    print("\n" + "="*60)
    print("✍️ EXECUTOR AGENT - DRAFTING PHASE")
    print("="*60)
    
    classification = state.get("classification")
    strategy = state.get("strategy")
    
    print(f"📊 Received Classification: {classification}")
    print(f"📋 Strategy Guidance: {strategy}")
    print(f"👤 Replying to: {state.get('email_sender')}")
    print("="*60)
    
    # Handle COLD leads with template - no LLM call needed
    if classification and classification.lower() == "cold":
        print("\n🔵 COLD LEAD DETECTED - Using company profile template")
        
        subject = state.get("email_subject", "")
        if not subject.startswith("Re:"):
            subject = f"Re: {subject}"
        
        return {
            "final_action": "send_reply",
            "email_draft": {
                "to": state.get("email_sender"),
                "subject": subject,
                "body": COLD_LEAD_TEMPLATE
            },
            "draft_type": "cold_template"  # Marker for frontend
        }
    
    # For HOT and WARM leads, use LLM to generate personalized response
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ FATAL ERROR: OPENAI_API_KEY not found.")
        print("   Please add OPENAI_API_KEY to backend/.env file")
        return {
            "final_action": "ignore",
            "reasoning": "Missing API Key. Please add OPENAI_API_KEY to your .env file."
        }

    # Initialize LLM
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    
    print(f"\n🤖 Initializing LLM for copywriting...")
    print(f"   Model: {model}")
    print(f"   Temperature: {temperature} (higher for creativity)")
    
    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        temperature=temperature
    )
    
    # Different prompts for HOT vs WARM
    if classification and classification.lower() == "hot":
        system_prompt = """You are a professional Email copywriter for a business.
        
        This is a HOT LEAD - urgent, high-priority response required!
        
        CRITICAL: You MUST return valid JSON with these exact fields:
        - "action": "send_reply"
        - "subject": the reply subject line (include "Re:" prefix)
        - "body": complete HTML email body
        
        HOT LEAD Guidelines:
        - Be urgent and professional
        - Acknowledge their specific needs immediately
        - Propose a concrete next step (call, meeting, demo)
        - Include availability or a calendar link mention
        - Keep it action-oriented
        - Use proper HTML formatting with <p> tags
        - Include a professional signature with contact info
        """
    else:  # WARM leads
        system_prompt = """You are a professional Email copywriter for a business.
        
        This is a WARM LEAD - show interest and provide value.
        
        CRITICAL: You MUST return valid JSON with these exact fields:
        - "action": "send_reply"
        - "subject": the reply subject line (include "Re:" prefix)
        - "body": complete HTML email body
        
        WARM LEAD Guidelines:
        - Be helpful and welcoming
        - Answer any questions they might have implied
        - Provide useful information about your services
        - Encourage further engagement
        - Soft call-to-action (learn more, schedule a chat)
        - Use proper HTML formatting with <p> tags
        - Include a professional signature
        """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt + "\n\nStrategy from analyst: {strategy}"),
        ("user", """Draft a reply to this email:
        
        From: {sender}
        Subject: {subject}
        Body: {body}
        
        Return ONLY valid JSON matching the required schema.""")
    ])
    
    parser = JsonOutputParser(pydantic_object=ExecutorOutput)
    chain = prompt | llm | parser
    
    try:
        print("\n📝 Generating professional email draft...")
        result = chain.invoke({
            "strategy": strategy,
            "sender": state.get("email_sender"),
            "subject": state.get("email_subject"),
            "body": state.get("email_body")
        })
        
        print("\n" + "="*60)
        print("📧 EMAIL DRAFT GENERATED")
        print("="*60)
        print(f"To: {state.get('email_sender')}")
        print(f"Subject: {result.get('subject')}")
        print(f"Action: {result.get('action', 'send_reply')}")
        print(f"\nBody Preview (first 200 chars):")
        print(f"{result.get('body', '')[:200]}...")
        print("="*60)
        print("✅ DECISION: Reply draft ready → Ready to send")
        print("="*60 + "\n")
        
        # Determine draft type for frontend
        draft_type = "hot_auto" if classification and classification.lower() == "hot" else "warm_review"
        
        return {
            "final_action": result.get("action", "send_reply"),
            "email_draft": {
                "to": state.get("email_sender"),
                "subject": result.get("subject"),
                "body": result.get("body")
            },
            "draft_type": draft_type
        }
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ EXECUTOR ERROR: {str(e)}")
        print("="*60)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Details: {str(e)}")
        print("="*60 + "\n")
        return {
            "final_action": "ignore",
            "reasoning": f"Drafting failed: {str(e)}"
        }
