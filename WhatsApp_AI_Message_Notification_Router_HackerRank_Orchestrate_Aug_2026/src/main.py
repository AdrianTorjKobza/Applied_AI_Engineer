"""Application CLI entry point implementing a Two-Stage Bootstrap Pattern for Windows resilience."""

import logging
import sys
from typing import Any

# =====================================================================
# STAGE 1: BOOTSTRAP LOGGING & WINDOWS STREAM CONFIGURATION
# Execute immediately before any heavy or native DLL imports occur.
# =====================================================================
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger("bootstrap")
logger.info("Stage 1 complete: Python interpreter initialized. Loading dependencies...")

# =====================================================================
# STAGE 2: SAFE DYNAMIC IMPORT & DEPENDENCY VERIFICATION
# =====================================================================
try:
    from src.config import settings
    from src.domain.exceptions import RouterDomainError
    from src.pipeline.orchestrator import MessageRoutingOrchestrator
    from src.utils.preflight import PreflightValidator

    logger.info("Stage 2 complete: All domain modules and native bindings loaded successfully.")
except (ImportError, OSError) as exc:
    logger.critical(
        "Fatal dependency load failure. On Windows, this is often caused by missing "
        "Microsoft Visual C++ Redistributable (2019-2022) DLLs required by faster-whisper or ChromaDB.\n"
        "Error details: %s",
        exc,
        exc_info=True,
    )
    sys.exit(1)
except Exception as exc:
    logger.critical("Unexpected error during module import: %s", exc, exc_info=True)
    sys.exit(1)


def main() -> int:
    """Executes pre-flight checks, system setup, and the async routing pipeline.

    Returns:
        int: System exit code (0 for success, 1 for domain/runtime errors).
    """
    logger.info("=== Starting WhatsApp Message Notification Router ===")
    logger.info("Project Root: %s", settings.base_dir)
    logger.info("Target Dataset Dir: %s", settings.dataset_dir)
    logger.info("Target Messages File: %s", settings.messages_csv_path)

    try:
        # Step 1: Execute pre-flight filesystem and dependency checks
        PreflightValidator.run_checks()

        # Step 2: Initialize pipeline orchestrator
        orchestrator = MessageRoutingOrchestrator()
        orchestrator.setup()

        # Step 3: Run async batch routing
        import asyncio

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