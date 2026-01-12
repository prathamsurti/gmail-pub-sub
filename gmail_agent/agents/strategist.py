import os
import json
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
    load_dotenv() # Fallback to default check

# Define output structure
class StrategistOutput(BaseModel):
    is_lead: bool = Field(description="Whether the email is a business lead or opportunity")
    classification: str = Field(description="Classification of the lead: 'Hot', 'Warm', 'Cold', or 'None' if not a lead")
    confidence_score: float = Field(description="Confidence score between 0.0 and 1.0")
    strategy: dict = Field(description="Strategic advice on how to reply")
    reasoning: str = Field(description="Brief explanation of the classification")

def strategist_node(state: dict):
    print("\n" + "="*60)
    print("🧠 STRATEGIST AGENT - ANALYSIS PHASE")
    print("="*60)
    print(f"📧 From: {state.get('email_sender')}")
    print(f"📋 Subject: {state.get('email_subject')}")
    print(f"📝 Body Preview: {state.get('email_body', '')[:100]}...")
    print("="*60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ FATAL ERROR: OPENAI_API_KEY not found in environment variables.")
        print("   Please add OPENAI_API_KEY to backend/.env file")
        return {
            "is_lead": False,
            "classification": "Error",
            "reasoning": "Missing API Key. Please add OPENAI_API_KEY to your .env file in root or backend/ folder.",
            "final_action": "ignore"
        }

    # Initialize LLM with OpenAI
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    
    print(f"🤖 Initializing LLM...")
    print(f"   Model: {model}")
    print(f"   Temperature: {temperature}")
    print(f"   Provider: OpenAI API")
    
    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        temperature=temperature
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert Email Lead Analyzer for a business.
        
        Your task: Analyze emails and determine if they represent genuine business opportunities.
        
        CRITICAL: You MUST return valid JSON with these exact fields:
        - "is_lead": true/false (is this a real business opportunity?)
        - "classification": "Hot", "Warm", "Cold", or "Spam"
        - "confidence_score": number between 0.0 and 1.0
        - "strategy": object with reply guidance (tone, key_points, urgency)
        - "reasoning": brief explanation of your decision
        
        Classification Guide:
        - HOT: Known contact/existing relationship + explicit buying intent, mentions specific budget/timeline, confirmed decision maker
        - WARM: Prior conversation or referral + genuine interest, personalized inquiry about specific services, exploring partnership
        - COLD: Unsolicited outreach, generic template email, no prior relationship, fishing for cheap rates, mass outreach patterns
        - SPAM: Marketing newsletters, obvious spam, completely unrelated content, automated messages
        
        RED FLAGS for COLD classification:
        - Generic greetings like "Hello team" or "Hi there" (not personalized)
        - Template language suggesting mass outreach
        - Asking for "rate cards" or wholesale pricing without context
        - Unreasonably low rates mentioned ($25-30/hr is below market)
        - No mention of referral or how they found you
        - Reselling/white-label requests from unknown sources
        
        For leads, provide specific strategy:
        {{"tone": "Professional & Urgent", "key_points": ["address timeline", "confirm capability"], "urgency": "high"}}
        
        For spam/cold, set is_lead=false and minimal strategy.
        """),
        ("user", """Analyze this email and return JSON:
        
        From: {sender}
        Subject: {subject}
        Body: {body}
        
        Return ONLY valid JSON matching the required schema.""")
    ])
    
    parser = JsonOutputParser(pydantic_object=StrategistOutput)
    chain = prompt | llm | parser
    
    try:
        print("\n🔍 Analyzing email content with LLM...")
        result = chain.invoke({
            "sender": state.get("email_sender"),
            "subject": state.get("email_subject"),
            "body": state.get("email_body")
        })
        
        print("\n" + "="*60)
        print("📊 ANALYSIS RESULTS")
        print("="*60)
        print(f"✓ Is Lead: {result.get('is_lead')}")
        print(f"✓ Classification: {result.get('classification')}")
        print(f"✓ Confidence Score: {result.get('confidence_score'):.2f}" if result.get('confidence_score') else "✓ Confidence Score: N/A")
        print(f"✓ Reasoning: {result.get('reasoning')}")
        print(f"✓ Strategy: {result.get('strategy')}")
        print("="*60)
        
        if result.get('is_lead'):
            print("✅ DECISION: Email is a LEAD → Passing to Executor Agent")
        else:
            print("⏭️  DECISION: Not a lead → Skipping reply")
        print("="*60 + "\n")
        
        return {
            "is_lead": result.get("is_lead", False),
            "classification": result.get("classification"),
            "confidence_score": result.get("confidence_score"),
            "strategy": result.get("strategy"),
            "reasoning": result.get("reasoning")
        }
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ STRATEGIST ERROR: {str(e)}")
        print("="*60)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Details: {str(e)}")
        print("="*60 + "\n")
        # Fallback safe state
        return {
            "is_lead": False, 
            "classification": "Error", 
            "reasoning": f"Analysis failed: {str(e)}",
            "final_action": "ignore"
        }
