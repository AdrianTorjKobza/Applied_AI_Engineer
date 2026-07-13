import requests
import json
from app.core.config import settings

class OllamaService:
    def __init__(self):
        self.base_url = settings.OLLAMA_URL
        self.text_model = settings.TEXT_MODEL

    def generate_text(self, prompt: str) -> str:
        """Calls the local Ollama API to generate text."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.text_model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except requests.exceptions.RequestException as e:
            # In a production environment, log this error
            return f"AI Generation Failed: {str(e)}"

    def generate_seo_metadata(self, text_content: str) -> dict:
        """Prompts Ollama to extract SEO metadata and output JSON."""
        prompt = f"""
        Based on the following marketing copy, generate SEO metadata in valid JSON format only. 
        Do not include markdown blocks or extra text.
        Required keys: "seo_tags" (list of strings), "alt_text" (string), "json_ld" (string representing schema).
        
        Copy: {text_content}
        """
        raw_response = self.generate_text(prompt)
        
        # Fallback in case the LLM doesn't format perfectly
        try:
            # Clean up potential markdown formatting from LLM
            clean_json = raw_response.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_json)
        except json.JSONDecodeError:
            return {
                "seo_tags": ["marketing", "product"],
                "alt_text": "Product image generated for campaign",
                "json_ld": "{}"
            }