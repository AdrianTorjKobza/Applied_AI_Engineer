"""LLM-as-judge scorer using a local Ollama model."""

from __future__ import annotations
import json
import re
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from llm_eval.models import JudgeConfig, JudgeScore, ModelResponse, Prompt

_JUDGE_SYSTEM = """\
You are a rigorous AI evaluator. Your task is to score a model's response to a given prompt.

Scoring criteria:
- **Relevance** (0-3): Does the response directly address what was asked?
- **Quality** (0-4): Is the writing clear, coherent, and well-structured?
- **Instruction following** (0-3): Does the response obey all explicit constraints?

Return ONLY valid JSON in this exact format (no extra text, no markdown):
{"score": <0-10 float>, "reasoning": "<one paragraph>"}
"""

_JUDGE_USER_TEMPLATE = """\
## Prompt
{user_prompt}

## System instruction (if any)
{system_prompt}

## Reference answer (if available)
{reference}

## Model response to evaluate
{response}

Score the model response.
"""

class LLMJudgeScorer:
    """Calls a local Ollama model to grade each (prompt, response) pair."""

    def __init__(self, config: JudgeConfig) -> None:
        self.config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout,
        )

    async def __aenter__(self) -> LLMJudgeScorer:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _call(self, user_content: str) -> str:
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": _JUDGE_SYSTEM},
                {"role": "user", "content": user_content},
            ],
            "stream": False,
            "options": {"temperature": self.config.temperature},
        }
        resp = await self._client.post("/api/chat", json=payload)
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    async def score(
        self,
        prompt: Prompt,
        response: ModelResponse,
    ) -> JudgeScore:
        user_content = _JUDGE_USER_TEMPLATE.format(
            user_prompt=prompt.user,
            system_prompt=prompt.system or "(none)",
            reference=prompt.reference or "(none)",
            response=response.output or "(empty — model returned an error)",
        )

        raw = ""
        score_val = 0.0
        reasoning = "Judge call failed."

        try:
            raw = await self._call(user_content)
            parsed = _extract_json(raw)
            score_val = float(parsed.get("score", 0.0))
            score_val = max(0.0, min(10.0, score_val))
            reasoning = str(parsed.get("reasoning", raw))
        except Exception as exc:  # noqa: BLE001
            reasoning = f"Judge error: {exc}"

        return JudgeScore(
            model_name=response.model_name,
            prompt_id=prompt.id,
            judge_model=self.config.model,
            score=score_val,
            reasoning=reasoning,
            raw_response=raw,
        )

def _extract_json(text: str) -> dict:
    """Try to parse JSON from the model response, with light cleanup."""
    text = text.strip()

    # Strip markdown fences if present.
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    # Find first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    
    if match:
        text = match.group(0)
    return json.loads(text)