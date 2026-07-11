# src/config.py
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    # Keycloak
    keycloak_url: str = "http://localhost:8080"
    realm: str = "agent-factory"
    client_id: str = "langgraph-api"
    # Using SecretStr prevents the value from leaking into logs
    client_secret: SecretStr 

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3"

    # Vault
    vault_url: str = "http://localhost:8200"

    @property
    def jwks_url(self) -> str:
        return f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/certs"

# Instantiate global settings
settings = Settings()