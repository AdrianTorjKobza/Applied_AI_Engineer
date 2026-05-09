"""CLI entry point — `llm-eval run / list-models / validate`."""

from __future__ import annotations
import asyncio
from pathlib import Path
import typer
import yaml
from rich.console import Console

from llm_eval.models import EvalConfig

app = typer.Typer(
    name="llm-eval",
    help="🔬 Local LLM comparison & evaluation harness (Ollama).",
    add_completion=False,
)
console = Console()


# ── helpers ───────────────────────────────────────────────────────

def _load_config(config_path: Path) -> EvalConfig:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return EvalConfig.model_validate(raw)


# ── commands ───────────────────────────────────────────────────────

@app.command()
def run(
    config: Path = typer.Option(
        "eval_config.yaml",
        "--config", "-c",
        help="Path to the YAML eval config file.",
        exists=True,
    ),
) -> None:
    """Run the full evaluation pipeline and generate an HTML report."""
    console.print(f"[bold cyan]llm-eval[/] — loading config from [yellow]{config}[/]\n")
    cfg = _load_config(config)

    from llm_eval.runner import run_eval
    asyncio.run(run_eval(cfg))


@app.command("list-models")
def list_models(
    base_url: str = typer.Option(
        "http://localhost:11434",
        "--base-url", "-u",
        help="Ollama base URL.",
    ),
) -> None:
    """List models currently available in the local Ollama instance."""
    import httpx

    try:
        resp = httpx.get(f"{base_url}/api/tags", timeout=10)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        if not models:
            console.print("[yellow]No models found. Pull one with: ollama pull llama3[/]")
            return
        console.print(f"\n[bold]Models in Ollama ({base_url}):[/]")
        for m in models:
            size_gb = m.get("size", 0) / 1e9
            console.print(f"  • [cyan]{m['name']}[/]  ({size_gb:.1f} GB)")
    except Exception as exc:
        console.print(f"[red]Could not reach Ollama:[/] {exc}")
        raise typer.Exit(1) from exc


@app.command()
def validate(
    config: Path = typer.Option(
        "eval_config.yaml",
        "--config", "-c",
        help="Path to the YAML eval config file.",
        exists=True,
    ),
) -> None:
    """Validate the eval config without running anything."""
    try:
        cfg = _load_config(config)
        console.print("[green]✓ Config is valid[/]")
        console.print(f"  run_name   : {cfg.run_name}")
        console.print(f"  models     : {[m.display_name for m in cfg.models]}")
        console.print(f"  dataset    : {cfg.dataset_path}")
        console.print(f"  judge      : {cfg.judge.model}")
        console.print(f"  scorers    : {[s.value for s in cfg.scorers]}")
    except Exception as exc:
        console.print(f"[red]✗ Invalid config:[/] {exc}")
        raise typer.Exit(1) from exc


@app.command("new-config")
def new_config(
    output: Path = typer.Option(
        "eval_config.yaml",
        "--output", "-o",
        help="Where to write the starter config.",
    ),
) -> None:
    """Scaffold a starter eval_config.yaml in the current directory."""
    template = Path(__file__).parent.parent / "eval_config.yaml"
    if template.exists():
        output.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        output.write_text(_DEFAULT_CONFIG, encoding="utf-8")
    console.print(f"[green]✓ Created[/] {output}")


_DEFAULT_CONFIG = """\
run_name: my_eval_run

models:
  - name: llama3:8b
    alias: LLaMA-3 8B
  - name: mistral:7b
    alias: Mistral 7B

judge:
  model: llama3:8b
  base_url: http://localhost:11434
  temperature: 0.0

dataset_path: datasets/sample/prompts.yaml
output_dir: reports
scorers:
  - llm_judge
max_concurrent: 3
"""


if __name__ == "__main__":
    app()
