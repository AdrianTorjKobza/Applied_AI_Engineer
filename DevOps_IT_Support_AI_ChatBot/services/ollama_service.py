import httpx
import json
from typing import AsyncGenerator
from core.config import settings

class OllamaService:
    """Handles communication with the local Ollama instance."""
    
    def __init__(self):
        # timeout=None ensures the backend never gives up on local model inference
        self.client = httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=None)

    async def stream_chat(self, prompt: str) -> AsyncGenerator[str, None]:
        """Streams text chunks directly from the local llama3 model."""

        payload = {
            "model": settings.ollama_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True
        }
        
        try:
            async with self.client.stream("POST", "/api/chat", json=payload) as response:
                # Catch API errors (like 404 Model Not Found) before they crash the JSON parser
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield f"\n\n**[Ollama API Error {response.status_code}]:** {error_text.decode('utf-8')}"
                    return

                async for line in response.aiter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            # Safely ignore malformed string chunks instead of crashing
                            continue
                            
        except httpx.ConnectError:
            yield "\n\n**[Connection Error]:** FastAPI could not reach Ollama. Is the Ollama app running on your machine?"