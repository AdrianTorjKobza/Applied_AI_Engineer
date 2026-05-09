# LLM Comparison & Evaluation Harness

> A local LLM comparison & evaluation harness powered by **Ollama**.
> Run any models you've pulled locally, score them with an LLM-as-judge, compare side-by-side, and get a polished HTML report.
---

## Features

| Feature | Details |
|---|---|
| **Local-first** | Runs entirely on your machine via [Ollama](https://ollama.com) — no API keys needed |
| **Multi-model comparison** | Compare any number of models in one run |
| **LLM-as-judge scoring** | A local judge model scores each response 0–10 with written reasoning |
| **Side-by-side diffs** | Every model pair shown together per prompt, filterable by pair |
| **HTML report** | Self-contained, dark-mode report with leaderboard, task breakdown, and diff viewer |
| **YAML-driven config** | Models, judge, dataset, and output dir all set in one file |

---

## Prerequisites

1. **Python 3.10+**
2. **[Ollama](https://ollama.com/download)** running locally (`ollama serve`)
3. At least two models pulled:

```bash
ollama pull llama3:8b
ollama pull mistral:7b
```

---

## Quick start

```bash
# Install
git clone
cd llm-eval-harness
pip install -e .

# List the Ollama models installed
llm-eval list-models

# Run the sample eval (uses eval_config.yaml + datasets/sample/prompts.yaml)
llm-eval run

# Open the report
open reports/sample_eval_*.html     # macOS
xdg-open reports/sample_eval_*.html # Linux
```

---

## Configuration

Edit `eval_config.yaml`:

```yaml
run_name: my_eval

models:
  - name: llama3:8b          # must match `ollama list`
    alias: "LLaMA-3 8B"
  - name: mistral:7b
    alias: "Mistral 7B"
  - name: phi3:mini
    alias: "Phi-3 Mini"

judge:
  model: llama3:8b           # model used to grade responses
  base_url: http://localhost:11434
  temperature: 0.0

dataset_path: datasets/sample/prompts.yaml
output_dir: reports
scorers:
  - llm_judge
max_concurrent: 3            # parallel requests per model
```

---

## Writing your own prompts

Create a YAML file anywhere and point `dataset_path` at it:

```yaml
prompts:
  - id: "my_q1"
    task_type: text_quality          # or: instruction_following
    user: "Explain quantum entanglement to a 10-year-old."

  - id: "my_q2"
    task_type: instruction_following
    system: "Reply only in bullet points."
    user: "What are the planets in our solar system?"
    reference: "Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune"
```

Supported `task_type` values: `text_quality`, `instruction_following`.

---

## CLI reference

```
Usage: llm-eval [COMMAND] [OPTIONS]

Commands:
  run           Run the full evaluation pipeline
  list-models   List models available in Ollama
  validate      Validate eval_config.yaml without running
  new-config    Scaffold a starter eval_config.yaml
```

```bash
llm-eval run --config path/to/eval_config.yaml
llm-eval list-models --base-url http://localhost:11434
llm-eval validate --config eval_config.yaml
llm-eval new-config --output my_config.yaml
```

---

## Project structure

```
llm-eval-harness/
├── llm_eval/
│   ├── adapters/
│   │   └── ollama.py          # Ollama async adapter
│   ├── tasks/
│   │   └── loader.py          # YAML dataset loader
│   ├── scorers/
│   │   ├── llm_judge.py       # LLM-as-judge scorer
│   │   ├── diff.py            # Side-by-side diff builder
│   │   └── summary.py         # Leaderboard statistics
│   ├── reporters/
│   │   ├── html.py            # HTML report renderer
│   │   └── report.html.j2     # Jinja2 report template
│   ├── cli.py                 # Typer CLI
│   ├── models.py              # Pydantic data models
│   └── runner.py              # Async eval pipeline
├── datasets/
│   └── sample/
│       └── prompts.yaml       # 10 sample prompts
├── eval_config.yaml           # Default config with two models
├── pyproject.toml
└── README.md
```

---
## 🧰 Tech Stack

| Layer | Library | Why |
|---|---|---|
| **Runtime / models** | [Ollama](https://ollama.com) | Run LLMs locally on CPU or GPU — one command to pull any model |
| **Data models** | [Pydantic v2](https://docs.pydantic.dev) | Typed, validated config and result objects throughout the pipeline |
| **CLI** | [Typer](https://typer.tiangolo.com) | Minimal, type-annotated CLI built on Click |
| **HTML templating** | [Jinja2](https://jinja.palletsprojects.com) | Logic-in-template report rendering with auto-escaping |
| **Slug generation** | [python-slugify](https://github.com/un33k/python-slugify) | Clean filenames for generated reports |

---