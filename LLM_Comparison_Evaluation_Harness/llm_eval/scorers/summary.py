"""Compute summary statistics from raw eval results."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean, stdev

from llm_eval.models import EvalResult


def compute_summary(result: EvalResult) -> dict:
    """
    Returns a dict like::

        {
            "models": {
                "llama3:8b": {
                    "avg_score": 7.4,
                    "std_score": 1.2,
                    "avg_latency_ms": 843.0,
                    "total_prompts": 10,
                    "errors": 0,
                },
                ...
            },
            "best_model": "llama3:8b",
            "task_breakdown": {
                "text_quality": {"llama3:8b": 7.8, ...},
                "instruction_following": {"llama3:8b": 7.0, ...},
            }
        }
    """
    prompt_task = {p.id: p.task_type.value for p in result.prompts}

    scores_by_model: dict[str, list[float]] = defaultdict(list)
    latency_by_model: dict[str, list[float]] = defaultdict(list)
    errors_by_model: dict[str, int] = defaultdict(int)
    task_scores: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for r in result.responses:
        latency_by_model[r.model_name].append(r.latency_ms)
        if r.error:
            errors_by_model[r.model_name] += 1

    for s in result.scores:
        scores_by_model[s.model_name].append(s.score)
        task = prompt_task.get(s.prompt_id, "unknown")
        task_scores[task][s.model_name].append(s.score)

    model_summaries = {}
    for model in latency_by_model:
        sc = scores_by_model.get(model, [])
        model_summaries[model] = {
            "avg_score": round(mean(sc), 2) if sc else None,
            "std_score": round(stdev(sc), 2) if len(sc) > 1 else 0.0,
            "avg_latency_ms": round(mean(latency_by_model[model]), 1),
            "total_prompts": len(latency_by_model[model]),
            "errors": errors_by_model[model],
        }

    best = max(
        model_summaries,
        key=lambda m: model_summaries[m]["avg_score"] or -1,
        default=None,
    )

    task_breakdown = {
        task: {
            model: round(mean(sc), 2)
            for model, sc in model_scores.items()
        }
        for task, model_scores in task_scores.items()
    }

    return {
        "models": model_summaries,
        "best_model": best,
        "task_breakdown": task_breakdown,
    }
