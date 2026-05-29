# Executes an ultra-fast, zero-token local system match using structured semantic validation rules before running any embedding operations.

import re

class LocalGuardrail:
    def __init__(self):
        # High-speed static pattern match
        self.banned_patterns = [
            r"(?i)\b(bypass\s+security|ignore\s+previous\s+instructions)\b",
            r"(?i)\b(how\s+to\s+make\s+a\s+(bomb|weapon|virus))\b"
        ]
        
        # Allowed topics (simple classifier check can be added if needed)
        self.allowed_keywords = ["company", "policy", "project", "code", "data", "how", "what"]

    def validate_query(self, query: str) -> tuple[bool, str]:
        """
        Validates the incoming query locally.
        Returns: (is_safe, error_or_sanitized_message)
        """
        # 1. Direct Safety Match
        for pattern in self.banned_patterns:
            if re.search(pattern, query):
                return False, "I cannot assist with queries that violate safety guidelines."
        
        # 2. Out of Domain/Off-topic Check (Basic heuristic for demonstration)
        tokens = query.lower().split()
        if not any(keyword in tokens for keyword in self.allowed_keywords):
            # We don't fail immediately, but we flag a warning or force strict filtering
            pass

        return True, query