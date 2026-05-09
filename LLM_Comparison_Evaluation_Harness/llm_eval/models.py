"""Shared Pydantic models used across the harness."""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TaskType(str, Enum):
    TEXT_QUALITY = "text_quality"
    INSTRUCTION_FOLLOWING = "instruction_following"


class ScorerType(str, Enum):
    LLM_JUDGE = "llm_judge"
    RULE_BASED = "rule_based"


# ---------------------------------------------------------------------------
# Config models
# ---------------------------------------------------------------------------

class ModelConfig(BaseModel):
    """A model to be evaluated."""
    name: str                          # e.g. "llama3:8b"
    alias: str | None = None           # human-friendly label
    base_url: str = "http://localhost:11434"
    timeout: float = 120.0
    extra_params: dict[str, Any] = Field(default_factory=dict)

    @property
    def display_name(self) -> str:
        return self.alias or self.name


class JudgeConfig(BaseModel):
    """Configuration for the LLM-as-judge scorer."""
    model: str = "llama3:8b"
    base_url: str = "http://localhost:11434"
    timeout: float = 120.0
    temperature: float = 0.0


class EvalConfig(BaseModel):
    """Top-level run configuration (mirrors eval_config.yaml)."""
    run_name: str = "eval_run"
    models: list[ModelConfig]
    judge: JudgeConfig = Field(default_factory=JudgeConfig)
    dataset_path: str = "datasets/sample/prompts.yaml"
    output_dir: str = "reports"
    scorers: list[ScorerType] = [ScorerType.LLM_JUDGE]
    max_concurrent: int = 3


# ---------------------------------------------------------------------------
# Runtime / result models
# ---------------------------------------------------------------------------

class Prompt(BaseModel):
    """A single evaluation prompt."""
    id: str
    task_type: TaskType
    system: str | None = None
    user: str
    reference: str | None = None      # optional gold answer for judges
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    """Raw response from a model for one prompt."""
    model_name: str
    prompt_id: str
    output: str
    latency_ms: float
    tokens_prompt: int | None = None
    tokens_completion: int | None = None
    error: str | None = None


class JudgeScore(BaseModel):
    """Score produced by the LLM judge for a single (model, prompt) pair."""
    model_name: str
    prompt_id: str
    judge_model: str
    score: float                       # 0–10
    reasoning: str
    raw_response: str


class DiffEntry(BaseModel):
    """Side-by-side comparison entry for two models on one prompt."""
    prompt_id: str
    prompt_text: str
    model_a: str
    model_b: str
    output_a: str
    output_b: str
    score_a: float | None = None
    score_b: float | None = None


class EvalResult(BaseModel):
    """Complete result for one evaluation run."""
    run_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    config: EvalConfig
    prompts: list[Prompt]
    responses: list[ModelResponse]
    scores: list[JudgeScore] = Field(default_factory=list)
    diffs: list[DiffEntry] = Field(default_factory=list)

    # Computed summary — populated by reporters
    summary: dict[str, Any] = Field(default_factory=dict)
