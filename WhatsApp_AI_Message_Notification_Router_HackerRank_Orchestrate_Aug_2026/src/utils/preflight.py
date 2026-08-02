"""Pre-flight validation utility to ensure filesystem and service readiness."""

import logging
import httpx
from src.config import settings
from src.domain.exceptions import RouterDomainError

logger = logging.getLogger(__name__)


class PreflightValidator:
    """Validates filesystem prerequisites, Ollama reachability, and model availability."""

    @classmethod
    def run_checks(cls) -> None:
        """Executes all pre-flight checks.

        Raises:
            RouterDomainError: If critical directories, input files, or required LLM models are missing.
        """
        logger.info("Executing pre-flight system checks...")
        cls._check_directories()
        cls._check_input_dataset()
        cls._check_ollama_connectivity_and_model()
        logger.info("Pre-flight checks completed successfully.")

    @classmethod
    def _check_directories(cls) -> None:
        """Verifies that necessary project directories exist."""
        required_dirs = [
            settings.dataset_dir,
            settings.media_dir,
            settings.images_dir,
            settings.audio_dir,
            settings.chroma_dir,
        ]
        for directory in required_dirs:
            if not directory.exists():
                logger.warning("Directory missing. Creating: %s", directory)
                directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _check_input_dataset(cls) -> None:
        """Verifies that messages.csv exists and is non-empty."""
        messages_file = settings.messages_csv_path
        if not messages_file.exists():
            error_msg = (
                f"Fatal: Required input file '{messages_file}' does not exist. "
                "Please place dataset files inside the 'dataset/' folder."
            )
            logger.error(error_msg)
            raise RouterDomainError(error_msg)

        if messages_file.stat().st_size == 0:
            error_msg = f"Fatal: Input file '{messages_file}' is empty (0 bytes)."
            logger.error(error_msg)
            raise RouterDomainError(error_msg)

        logger.info(
            "Input dataset verified: %s (%d bytes)",
            messages_file,
            messages_file.stat().st_size,
        )

    @classmethod
    def _check_ollama_connectivity_and_model(cls) -> None:
        """Verifies that Ollama is reachable AND that the required model is installed."""
        tags_url = f"{settings.ollama_base_url}/api/tags"
        logger.debug("Checking Ollama availability and model registry at %s...", tags_url)
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(tags_url)
                response.raise_for_status()
                data = response.json()

                installed_models = [
                    model.get("name", "") for model in data.get("models", [])
                ]
                logger.debug("Installed Ollama models: %s", installed_models)

                # Check exact match or base tag match (e.g., 'qwen2.5-vl:7b' matching 'qwen2.5-vl:7b:latest')
                target_model = settings.ollama_model
                is_installed = any(
                    name == target_model or name.startswith(f"{target_model}:")
                    for name in installed_models
                )

                if not is_installed:
                    error_msg = (
                        f"Fatal: Required Ollama model '{target_model}' is NOT installed.\n"
                        f"Available models in your Ollama instance: {installed_models or 'None'}.\n"
                        f"Please run the following command in your terminal and try again:\n"
                        f"    ollama pull {target_model}"
                    )
                    logger.error(error_msg)
                    raise RouterDomainError(error_msg)

                logger.info("Ollama is reachable and model '%s' is verified.", target_model)

        except httpx.HTTPError as exc:
            logger.warning(
                "Ollama daemon unreachable at %s (%s). "
                "Pipeline will fallback to default heuristic rules if LLM requests fail.",
                settings.ollama_base_url,
                exc,
            )