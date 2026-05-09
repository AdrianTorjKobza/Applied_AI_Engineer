"""Render evaluation results to a self-contained HTML report."""
from __future__ import annotations
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from slugify import slugify
from llm_eval.models import EvalResult

_TEMPLATE_DIR = Path(__file__).parent
_TEMPLATE_NAME = "report.html.j2"

def render_html_report(result: EvalResult, output_dir: str | Path = "reports") -> Path:
    """
    Write an HTML report to *output_dir* and return the file path.

    The file is named  ``<run_name>_<timestamp>.html``.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    ts = result.timestamp.strftime("%Y%m%d_%H%M%S")
    slug = slugify(result.run_name)
    filename = f"{slug}_{ts}.html"
    dest = out / filename

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template(_TEMPLATE_NAME)

    # Pre-compute data the template needs.
    model_names: list[str] = sorted({r.model_name for r in result.responses})
    ranked_models = sorted(
        model_names,
        key=lambda m: result.summary.get("models", {}).get(m, {}).get("avg_score") or -1,
        reverse=True,
    )
    
    task_types = sorted({p.task_type.value for p in result.prompts})
    prompt_task_map = {p.id: p.task_type.value for p in result.prompts}

    html = template.render(
        result=result,
        summary=result.summary,
        model_names=model_names,
        ranked_models=ranked_models,
        task_types=task_types,
        prompt_task_map=prompt_task_map,
    )
    dest.write_text(html, encoding="utf-8")
    return dest
