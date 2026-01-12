from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict):
    # Input
    email_sender: str
    email_subject: str
    email_body: str
    email_id: str
    thread_id: str
    
    # Internal Analysis (Strategist Output)
    is_lead: bool
    classification: Optional[str]  # "Hot", "Warm", "Cold"
    confidence_score: Optional[float]
    strategy: Optional[Dict[str, Any]]
    
    # Execution (Executor Output)
    email_draft: Optional[Dict[str, str]]  # {to, subject, body}
    
    # Final Output
    final_action: str  # "send_reply", "mark_read", "ignore"
    reasoning: Optional[str]
