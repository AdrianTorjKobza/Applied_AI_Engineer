from pydantic import BaseModel, Field

class WebhookPayload(BaseModel):
    ticket_id: str
    source: str = Field(description="e.g., zendesk, jira, internal")
    customer_email: str
    subject: str
    description: str

class WebhookResponse(BaseModel):
    status: str
    thread_id: str