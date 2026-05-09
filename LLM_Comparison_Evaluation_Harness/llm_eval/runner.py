"""Main eval runner — orchestrates adapters, scorers, and reporters."""

from __future__ import annotations
import asyncio
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from llm_eval.adapters.ollama import OllamaAdapter
from llm_eval.models import (
    EvalConfig,
    EvalResult,
    JudgeScore,
    ModelResponse,
    ScorerType,
)
from llm_eval.reporters.html import render_html_report
from llm_eval.scorers.diff import build_diffs
from llm_eval.scorers.llm_judge import LLMJudgeScorer
from llm_eval.scorers.summary import compute_summary
from llm_eval.tasks.loader import load_dataset

console = Console()

async def run_eval(config: EvalConfig) -> EvalResult:
    """Run the full evaluation pipeline and return an EvalResult."""

    # ── 1. Load prompts ────────────────────────────────────────────
    prompts = load_dataset(config.dataset_path)
    console.print(f"[bold cyan]Loaded {len(prompts)} prompts from[/] {config.dataset_path}")

    # ── 2. Generate responses ──────────────────────────────────────
    console.print(f"\n[bold]Generating responses from {len(config.models)} model(s)…[/]")
    all_responses: list[ModelResponse] = []

    semaphore = asyncio.Semaphore(config.max_concurrent)

    async def _generate_one(adapter: OllamaAdapter, prompt):
        async with semaphore:
            return await adapter.generate(
                prompt_id=prompt.id,
                user=prompt.user,
                system=prompt.system,
            )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        console=console,
    ) as progress:
        for model_cfg in config.models:
            task_id = progress.add_task(
                f"[cyan]{model_cfg.display_name}[/]", total=len(prompts)
            )
            async with OllamaAdapter(model_cfg) as adapter:
                tasks = [_generate_one(adapter, p) for p in prompts]
                for coro in asyncio.as_completed(tasks):
                    resp = await coro
                    all_responses.append(resp)
                    progress.advance(task_id)

    # ── 3. Score with LLM judge ────────────────────────────────────
    all_scores: list[JudgeScore] = []
    if ScorerType.LLM_JUDGE in config.scorers:
        console.print(
            f"\n[bold]Scoring with judge model[/] [cyan]{config.judge.model}[/]…"
        )
        prompt_map = {p.id: p for p in prompts}
        async with LLMJudgeScorer(config.judge) as judge:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                console=console,
            ) as progress:
                task_id = progress.add_task("Judging", total=len(all_responses))
                sem2 = asyncio.Semaphore(config.max_concurrent)

                async def _score_one(resp: ModelResponse) -> JudgeScore:
                    async with sem2:
                        p = prompt_map[resp.prompt_id]
                        score = await judge.score(p, resp)
                        progress.advance(task_id)
                        return score

                score_tasks = [_score_one(r) for r in all_responses]
                all_scores = await asyncio.gather(*score_tasks)

    # ── 4. Build result object ─────────────────────────────────────
    result = EvalResult(
        run_name=config.run_name,
        config=config,
        prompts=prompts,
        responses=all_responses,
        scores=list(all_scores),
    )

    # ── 5. Compute diffs & summary ─────────────────────────────────
    result.diffs = build_diffs(result)
    result.summary = compute_summary(result)

    # ── 6. Print CLI summary table ─────────────────────────────────
    _print_summary(result)

    # ── 7. Render HTML report ──────────────────────────────────────
    report_path = render_html_report(result, output_dir=config.output_dir)
    console.print(f"\n[bold green]✓ Report saved →[/] {report_path.resolve()}")

    return result

def _print_summary(result: EvalResult) -> None:
    """Print a rich summary table to the console."""
    console.print()
    table = Table(title="Evaluation Summary", show_header=True, header_style="bold cyan")
    table.add_column("Rank", style="bold", width=5)
    table.add_column("Model", style="white")
    table.add_column("Avg Score", justify="right")
    table.add_column("Std Dev", justify="right", style="dim")
    table.add_column("Avg Latency", justify="right", style="dim")
    table.add_column("Errors", justify="right")

    ranked = sorted(
        result.summary.get("models", {}).items(),
        key=lambda kv: kv[1].get("avg_score") or -1,
        reverse=True,
    )
    medals = ["🥇", "🥈", "🥉"]
    for idx, (model, stats) in enumerate(ranked):
        rank = medals[idx] if idx < 3 else str(idx + 1)
        score = stats.get("avg_score")
        score_str = f"{score:.2f}" if score is not None else "N/A"
        table.add_row(
            rank,
            model,
            score_str,
            f"± {stats.get('std_score', 0):.2f}",
            f"{stats.get('avg_latency_ms', 0):.0f} ms",
            str(stats.get("errors", 0)),
        )
    console.print(table)