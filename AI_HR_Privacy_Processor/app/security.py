from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from app import config

# Expect the client to send an "X-API-Key" header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Validates the incoming API key against our centralized configuration."""
    
    # Compare the client's key against the loaded config key
    if api_key != config.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return api_key