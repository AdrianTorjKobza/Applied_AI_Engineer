"""Build side-by-side diff entries between model pairs."""

from __future__ import annotations
from itertools import combinations
from llm_eval.models import DiffEntry, EvalResult, ModelResponse

def build_diffs(result: EvalResult) -> list[DiffEntry]:
    """
    For every unique pair of models and every prompt, create a DiffEntry
    that places their outputs side by side with judge scores.
    """
    # Index responses and scores
    resp_index: dict[tuple[str, str], ModelResponse] = {
        (r.model_name, r.prompt_id): r for r in result.responses
    }
    score_index: dict[tuple[str, str], float] = {
        (s.model_name, s.prompt_id): s.score for s in result.scores
    }
    {p.id: p for p in result.prompts}

    model_names = list({r.model_name for r in result.responses})
    diffs: list[DiffEntry] = []

    for model_a, model_b in combinations(model_names, 2):
        for prompt in result.prompts:
            pid = prompt.id
            ra = resp_index.get((model_a, pid))
            rb = resp_index.get((model_b, pid))
            if ra is None or rb is None:
                continue
            diffs.append(
                DiffEntry(
                    prompt_id=pid,
                    prompt_text=prompt.user,
                    model_a=model_a,
                    model_b=model_b,
                    output_a=ra.output or f"[ERROR] {ra.error}",
                    output_b=rb.output or f"[ERROR] {rb.error}",
                    score_a=score_index.get((model_a, pid)),
                    score_b=score_index.get((model_b, pid)),
                )
            )
    return diffs