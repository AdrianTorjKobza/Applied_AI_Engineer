from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class EventAttributes(BaseModel):
    duration_seconds: Optional[int] = 0
    scrolled_percentage: Optional[int] = 0

class UserEvent(BaseModel):
    user_id: str
    event_type: str = Field(..., description="e.g., click, dwell_time, cart_add")
    product_id: str
    category: str
    attributes: EventAttributes
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CategoryAffinity(BaseModel):
    running_gear: float = Field(default=0.0)
    weightlifting: float = Field(default=0.0)
    outdoor: float = Field(default=0.0)