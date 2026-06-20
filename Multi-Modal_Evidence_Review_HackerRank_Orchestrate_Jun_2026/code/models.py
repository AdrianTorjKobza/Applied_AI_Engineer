# To ensure compile-time security and clear knowledge representation, we will map out the domain logic using Pydantic models.
# We need structures to hold our raw input datasets: user_history.csv, evidence_requirements.csv, and the target schema required by the problem statement.

from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# --- Input Schemas ---
class UserHistory(BaseModel):
    user_id: str
    past_claim_count: int
    accept_claim: int
    manual_review_claim: int
    rejected_claim: int
    last_90_days_claim_count: int
    history_flags: str
    history_summary: str

class EvidenceRequirement(BaseModel):
    requirement_id: str
    claim_object: Literal["car", "laptop", "package", "all"]
    applies_to: str
    minimum_image_evidence: str

# --- Intermediate VLM Extraction Schema ---
class VLMExtraction(BaseModel):
    image_id: str
    object_detected: str = Field(description="The core object type visible in the image.")
    visible_part: str = Field(description="The specific part of the object visible.")
    visible_issue: str = Field(description="The clear visual issue or damage detected.")
    severity_assessment: Literal["none", "low", "medium", "high", "unknown"]
    is_blurry_or_low_quality: bool
    is_manipulated_or_suspicious: bool
    visual_justification: str = Field(description="1-2 sentences stating exactly what is observed in this specific image.")

# --- Final Production Output Schema ---
class FinalClaimOutput(BaseModel):
    user_id: str
    image_paths: str
    user_claim: str
    claim_object: Literal["car", "laptop", "package"]
    evidence_standard_met: bool
    evidence_standard_met_reason: str
    risk_flags: str  # Semicolon-separated or "none"
    issue_type: Literal["dent", "scratch", "crack", "glass_shatter", "broken_part", "missing_part", "torn_packaging", "crushed_packaging", "water_damage", "stain", "none", "unknown"]
    object_part: str # Allowed values per-category checked downstream
    claim_status: Literal["supported", "contradicted", "not_enough_information"]
    claim_status_justification: str
    supporting_image_ids: str  # Semicolon-separated or "none"
    valid_image: bool
    severity: Literal["none", "low", "medium", "high", "unknown"]