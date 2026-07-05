from pydantic import BaseModel

class HRDocumentRequest(BaseModel):
    department: str
    task: str = "summarize_and_redact"
    document_text: str