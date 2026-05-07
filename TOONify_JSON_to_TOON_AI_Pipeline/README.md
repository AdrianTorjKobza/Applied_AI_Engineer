# 🚀 TOONify

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)
![AI](https://img.shields.io/badge/focus-Applied%20AI-purple)
![Tokens](https://img.shields.io/badge/token%20reduction-30--60%25-orange)

📉 Reduce LLM token costs by up to **40%** with smarter data formatting.

---

## 🔷 Overview

**TOONify_AI** is a Python library that optimizes structured data for Large Language Models (LLMs) by automatically selecting the most token-efficient format:

- JSON (default)
- TOON (Token-Oriented Object Notation)

Instead of blindly sending JSON to models, TOONify helps you:
- reduce token usage  
- lower API costs  
- improve structure clarity for LLMs  

---

## 🔷 Why this matters

JSON was designed for APIs, not LLMs.

Problems with JSON:
- repeated keys increase token usage  
- unnecessary syntax adds noise  
- higher cost per request  

**TOONify_AI solves this by:**
- converting JSON → TOON when beneficial  
- estimating token usage using `tiktoken`  
- recommending the best format automatically  

---

## 🔷 What is TOON?

**Token-Oriented Object Notation (TOON)** is a compact format optimized for LLMs.

Instead of repeating keys in every object, TOON:
- defines schema once  
- streams values efficiently  

### Example

**JSON**
```json
[
  {"id": 1, "name": "Alice"},
  {"id": 2, "name": "Bob"}
]
```

**TOON**
```
data[2]{id,name}:
  1,Alice
  2,Bob
```

👉 Same data, fewer tokens.

---

## 🔷 Features

- JSON → TOON conversion  
- Token estimation (LLM-aware)  
- Smart format recommendation engine  
- CLI support

---

## 🔷 Installation

```bash
git clone
cd TOONify_JSON_to_TOON_AI_Pipeline
pip install -e .
```
---

## 🔷 Quick Start

### Python Usage

```python
from src.optimize import optimize

data = [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"},
    {"id": 3, "name": "Charlie"}
]

result = optimize(data)

print(result)
```

---

### Example Output

```json
{
  "recommended_format": "TOON",
  "reason": "Uniform array with repeated keys",
  "json_tokens": 120,
  "toon_tokens": 68,
  "savings_percent": 43.33,
  "output": "data[3]{id,name}:\n  1,Alice\n  2,Bob\n  3,Charlie"
}
```

---

## 🔷 CLI Usage

```bash
python -m cli.main data/data.json
```

### Output

```
--- Analysis ---
Recommended: TOON
Reason: Uniform array with repeated keys
JSON tokens: 1240
TOON tokens: 710
Savings: 42.7%

--- TOON Output ---
data[3]{id,name}:
  1,Alice
  2,Bob
  3,Charlie
```

---

## 🔷 Token Savings Visualization

```
JSON  | ██████████████████████████████████████████ 1240 tokens
TOON  | ████████████████████████                  710 tokens
```

**Savings: ~42.7%**

---

## 🔷 How it works

### 1. Structure Analysis
Detects:
- arrays vs objects  
- uniform schemas  
- nesting depth  

### 2. Token Estimation
Uses `tiktoken` for model-aware token counting  

### 3. Recommendation Engine
Chooses format based on:
- repetition  
- structure simplicity  
- expected savings  

---

## 🔷 When TOON works best

- uniform arrays of objects  
- repeated keys  
- flat or moderately nested structures (up to 3) 

---

## 🔷 When JSON is better

- deeply nested data  
- inconsistent schemas  
- irregular structures  

---

## 🔷 Use Cases

- prompt engineering  
- RAG pipelines  
- LLM tool inputs  
- structured memory  
- reducing token costs in production systems  

---

## 🔷 Roadmap

- [ ] Python Library
- [ ] Nested TOON support
- [ ] FastAPI and "try it out" web interface
- [ ] Benchmark

---

## 🔷 License

MIT License

---
