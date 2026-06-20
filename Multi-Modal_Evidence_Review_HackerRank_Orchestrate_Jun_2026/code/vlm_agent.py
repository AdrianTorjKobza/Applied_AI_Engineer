# The standalone VLMAgent. This agent connects directly to the local Ollama service (http://localhost:11434/api/chat).
# We will feed qwen2.5-vl:7b a highly disciplined system prompt instructing it to act as an objective claims inspector.
# It will evaluate the image alongside the user's textual claim string, then extract the key visual findings into our intermediate VLMExtraction JSON layout.

import requests
from utils import encode_image_to_base64
from models import VLMExtraction

class VLMAgent:
    def __init__(self, model_name: str = "qwen2.5vl:7b", host: str = "http://localhost:11434"):
        self.api_url = f"{host}/api/chat"
        self.model_name = model_name

    def process_image(self, image_path: str, user_claim: str) -> VLMExtraction:
        try:
            base64_image = encode_image_to_base64(image_path)
        except Exception as e:
            return VLMExtraction(
                image_id=image_path.split('/')[-1],
                object_detected="unknown",
                visible_part="unknown",
                visible_issue="none",
                severity_assessment="unknown",
                is_blurry_or_low_quality=True,
                is_manipulated_or_suspicious=False,
                visual_justification=f"Image load failure: {str(e)}"
            )

        system_instruction = (
            "You are an expert visual claims inspector. You do NOT output code or JSON. "
            "Write a single, concise paragraph describing exactly what you see in the image."
        )

        user_prompt = f"""
        User Claim: "{user_claim}"
        
        Act as a forensic visual inspector. Do not output JSON. Output a structured text report using exactly these bullet points:
        - OBJECT DETECTED: (car, laptop, package, or none)
        - RELEVANT PART: (e.g., windshield, screen, corner)
        - DAMAGE ANALYSIS: (Be highly specific. Is there a scratch, dent, tear, or is it perfectly clean?)
        - IMAGE QUALITY: (Is the image blurry, dark, or clear?)
        - CONCLUSION: (Does the image visually confirm the user's claim?)
        """

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_instruction},
                {
                    "role": "user", 
                    "content": user_prompt,
                    "images": [base64_image]
                }
            ],
            "options": {"temperature": 0.0},
            "stream": False
        }

        try:
            # High timeout to absorb cold-start loads safely
            response = requests.post(self.api_url, json=payload, timeout=180)
            response.raise_for_status()
            
            raw_text = response.json()["message"]["content"].strip()
            
            return VLMExtraction(
                image_id=image_path.split('/')[-1],
                object_detected="See observations",
                visible_part="See observations",
                visible_issue="See observations",
                severity_assessment="unknown",
                is_blurry_or_low_quality=False,
                is_manipulated_or_suspicious=False,
                visual_justification=raw_text
            )
            
        except Exception as err:
            return VLMExtraction(
                image_id=image_path.split('/')[-1],
                object_detected="unknown",
                visible_part="unknown",
                visible_issue="unknown",
                severity_assessment="unknown",
                is_blurry_or_low_quality=False,
                is_manipulated_or_suspicious=False,
                visual_justification=f"VLM Text Generation Error: {str(err)}"
            )