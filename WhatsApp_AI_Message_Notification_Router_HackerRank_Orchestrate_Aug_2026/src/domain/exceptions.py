"""Domain-specific custom exceptions."""


class RouterDomainError(Exception):
    """Base exception for domain errors in the router application."""


class MediaProcessingError(RouterDomainError):
    """Raised when audio or image processing fails."""


class LLMInferenceError(RouterDomainError):
    """Raised when external LLM inference fails."""


class VectorStoreError(RouterDomainError):
    """Raised when vector store initialization or querying fails."""