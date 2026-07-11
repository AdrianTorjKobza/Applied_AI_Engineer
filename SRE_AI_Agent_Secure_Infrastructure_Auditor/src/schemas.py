from pydantic import BaseModel
from typing import TypedDict

class PromptRequest(BaseModel):
    """Payload for incoming API requests."""
    prompt: str

class AgentState(TypedDict):
    """The LangGraph state object passed between nodes."""
    messages: list
    dummy_api_key: str