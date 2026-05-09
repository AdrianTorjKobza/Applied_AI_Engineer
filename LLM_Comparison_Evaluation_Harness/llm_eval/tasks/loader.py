"""Load evaluation prompts from YAML dataset files."""

from __future__ import annotations
from pathlib import Path
import yaml

from llm_eval.models import Prompt, TaskType


def load_dataset(path: str | Path) -> list[Prompt]:
    """
    Load prompts from a YAML file.

    Expected format::

        prompts:
          - id: "q1"
            task_type: text_quality
            user: "Write a short poem about the sea."
            reference: null          # optional
          - id: "q2"
            task_type: instruction_following
            system: "You are a helpful assistant."
            user: "List 3 benefits of regular exercise."
            reference: "1. ... 2. ... 3. ..."
    """
    raw = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(raw) # Convert text into a standard Python Dictionary.

    prompts: list[Prompt] = []

    for entry in data.get("prompts", []):
        task_type = TaskType(entry.get("task_type", "text_quality"))
        prompts.append(
            Prompt(
                id=str(entry["id"]),
                task_type=task_type,
                system=entry.get("system"),
                user=entry["user"],
                reference=entry.get("reference"),
                metadata=entry.get("metadata", {}),
            )
        )
    return prompts