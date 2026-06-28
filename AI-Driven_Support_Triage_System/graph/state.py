from typing import TypedDict, Optional

class TriageState(TypedDict):
    thread_id: str
    ticket_id: str
    description: str
    category: Optional[str]
    draft_response: Optional[str]
    confidence_score: Optional[float]
    status: str             # 'processing', 'requires_review', 'resolved', 'escalated'
    human_action: Optional[str]  # 'approve' or 'reject'