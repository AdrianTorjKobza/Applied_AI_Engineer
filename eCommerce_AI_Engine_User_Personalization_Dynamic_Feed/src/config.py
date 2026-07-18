from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # App Config
    app_name: str = "Event-Driven AI Recommendation Engine API"
    environment: str = "development"
    debug: bool = False

    # Redis Config
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"

    # Postgres Config
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # AI Config
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # Pydantic v2 specific configuration to load from .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache
def get_settings() -> Settings:
    """
    Caches the settings so we don't read the .env file on every import.
    """
    return Settings()

# Global settings instance to be imported across the app
settings = get_settings()