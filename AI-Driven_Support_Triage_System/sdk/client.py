import httpx
from typing import Dict, Any

class TriageClient:
    """Internal Python SDK for teams to submit support tickets."""
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    async def submit_ticket(self, source: str, ticket_id: str, email: str, subject: str, description: str) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/api/v1/tickets/webhook"

        payload = {
            "source": source,
            "ticket_id": ticket_id,
            "customer_email": email,
            "subject": subject,
            "description": description
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()