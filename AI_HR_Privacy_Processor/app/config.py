import os
from dotenv import load_dotenv

# Force the server to load the .env file when running outside of Docker
load_dotenv()

# Application Settings
API_KEY = os.getenv("MOCK_API_KEY", "default_insecure_key")
TARGET_MODEL = os.getenv("TARGET_MODEL", "phi3")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

# Telemetry Settings
TELEMETRY_LOG_DIR = os.getenv("TELEMETRY_LOG_DIR", "logs")