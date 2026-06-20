# Builds a structured payload containing the user's history and the minimum evidence requirements,
# then asks qwen2.5:7b to reason about the final claim parameters using a strict, zero-temperature schema constraint.

import requests
import json
from typing import List, Optional
from models import VLMExtraction, UserHistory, EvidenceRequirement

class LogicAgent:
    def __init__(self, model_name: str = "qwen2.5:7b", host: str = "http://localhost:11434"):
        self.api_url = f"{host}/api/chat"
        self.model_name = model_name

    def synthesize_claim(
        self,
        user_id: str,
        user_claim: str,
        claim_object: str,
        image_paths: str,
        vlm_results: List[VLMExtraction],
        user_history: Optional[UserHistory],
        requirements: List[EvidenceRequirement]
    ) -> dict: 
        
        vlm_summary = []
        for res in vlm_results:
            vlm_summary.append(
                f"- Image [{res.image_id}]: Observations: {res.visual_justification}"
            )
        vlm_summary_str = "\n".join(vlm_summary)

        if user_history:
            history_str = (
                f"Past Claims Total: {user_history.past_claim_count}, Accepted: {user_history.accept_claim}, "
                f"Rejected: {user_history.rejected_claim}, Manual Reviews: {user_history.manual_review_claim}.\n"
                f"Flags: {user_history.history_flags}\nSummary: {user_history.history_summary}"
            )
        else:
            history_str = "No existing profile. This is a brand new user profile."

        req_summary = []
        for req in requirements:
            req_summary.append(f"- Applies to: {req.applies_to}. Min Evidence Req: {req.minimum_image_evidence}")
        req_summary_str = "\n".join(req_summary) if req_summary else "No explicit baseline minimum constraints."

        system_instruction = (
            "You are a Senior Insurance Adjuster and System Rule Synthesizer.\n"
            "Analyze visual inspection notes against user records and output an evaluation JSON.\n"
            "EXAMPLE OUTPUT:\n"
            "{\"reasoning_scratchpad\": \"The user claims a scratched door. Visual notes confirm a deep scratch on the left door. History shows no fraud.\", "
            "\"evidence_standard_met\": true, \"evidence_standard_met_reason\": \"clear photo provided\", \"risk_flags\": \"none\", "
            "\"issue_type\": \"scratch\", \"object_part\": \"door\", \"claim_status\": \"supported\", \"claim_status_justification\": \"Confirmed visually\", "
            "\"supporting_image_ids\": \"img_1.jpg\", \"valid_image\": true, \"severity\": \"medium\"}\n"
            "Do not output conversational filler text."
        )

        user_prompt = f"""
        === CLAIM CONTEXT ===
        Claim Object Type: {claim_object}
        User Claim Description: "{user_claim}"
        Submitted Image Filenames: {image_paths}
        
        === STAGE 1 VISUAL NOTES ===
        {vlm_summary_str}
        
        === USER ACCOUNT RISK PROFILE ===
        {history_str}
        
        === INSURANCE POLICY EVIDENCE REQUIREMENTS ===
        {req_summary_str}
        
        === LOGICAL CONSTRAINTS ===
        1. 'evidence_standard_met': true/false based on image count vs requirements.
        2. 'risk_flags': select from [none, blurry_image, cropped_or_obstructed, low_light_or_glare, wrong_angle, wrong_object, wrong_object_part, damage_not_visible, claim_mismatch, possible_manipulation, user_history_risk, manual_review_required].
        3. 'claim_status': supported, contradicted, or not_enough_information.
        4. 'issue_type': [dent, scratch, crack, glass_shatter, broken_part, missing_part, torn_packaging, crushed_packaging, water_damage, stain, none, unknown].
        5. 'object_part': Must match valid parts for {claim_object}.
        6. 'severity': [none, low, medium, high, unknown].
        7. MULTI-IMAGE RULE: If *any* single image explicitly supports the claim, the claim is 'supported'.
        
        Return ONLY a JSON object containing these precise analytical keys:
        {{
            "reasoning_scratchpad": "Write 2-3 sentences evaluating the visual notes against the user claim.",
            "evidence_standard_met": true,
            "evidence_standard_met_reason": "string reason",
            "risk_flags": "none",
            "issue_type": "dent",
            "object_part": "unknown",
            "claim_status": "supported",
            "claim_status_justification": "concise explanation grounded in the visual evidence",
            "supporting_image_ids": "none",
            "valid_image": true,
            "severity": "none"
        }}
        """

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            "options": {"temperature": 0.0},
            "stream": False,
            "format": "json"
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=180)
            response.raise_for_status()
            return json.loads(response.json()["message"]["content"])
        except Exception as err:
            return {
                "evidence_standard_met": False,
                "evidence_standard_met_reason": "System synthesis timeout",
                "risk_flags": "none",
                "issue_type": "unknown",
                "object_part": "unknown",
                "claim_status": "not_enough_information",
                "claim_status_justification": f"Error: {str(err)}",
                "supporting_image_ids": "none",
                "valid_image": False,
                "severity": "unknown"
            }