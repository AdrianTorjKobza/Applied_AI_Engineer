"""Application CLI entry point with forced console logging and pre-flight validation."""

import asyncio
import logging
import sys
from src.config import settings
from src.domain.exceptions import RouterDomainError
from src.pipeline.orchestrator import MessageRoutingOrchestrator
from src.utils.preflight import PreflightValidator


def _configure_logging() -> None:
    """Configures structured console logging with force=True to override library handlers."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
        force=True,  # Overrides any logging handlers set by imported libraries
    )


def main() -> int:
    """Executes the pre-flight checks, system setup, and pipeline runner.

    Returns:
        int: System exit code (0 for success, 1 for domain/runtime errors).
    """
    _configure_logging()
    logger = logging.getLogger("main")
    logger.info("=== Starting WhatsApp Message Notification Router ===")
    logger.info("Project Root: %s", settings.base_dir)
    logger.info("Target Dataset: %s", settings.dataset_dir)

    try:
        # 1. Verify filesystem & dependencies before initializing heavy models
        PreflightValidator.run_checks()

        # 2. Setup orchestration pipeline
        orchestrator = MessageRoutingOrchestrator()
        orchestrator.setup()

        # 3. Execute async routing
        asyncio.run(orchestrator.run())
        logger.info("=== Application Finished Successfully ===")
        return 0

    except RouterDomainError as exc:
        logger.error("Domain validation or execution error: %s", exc)
        return 1
    except Exception as exc:
        logger.exception("Unexpected fatal error occurred during execution: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())