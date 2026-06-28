import os
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class LocalLLMClient:
    """Dependency Inversion: Abstraction for our local Llama instance."""
    def __init__(self, base_url: str = "http://localhost:11434/api/generate"):
        self.base_url = base_url

        self.model = os.getenv("AI_MODEL_NAME", "llama3:8b")
        print(f"[Config] Initializing LLM Client with model: {self.model}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate(self, prompt: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            response = await client.post(self.base_url, json=payload, timeout=180.0)
            response.raise_for_status()
            return response.json()