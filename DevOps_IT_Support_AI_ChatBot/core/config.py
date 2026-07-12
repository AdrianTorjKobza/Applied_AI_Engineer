from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings and environment configuration management."""
    app_name: str = "AI Chat Bot - IT & DevOps Troubleshooter API"
    
    env: str = "development" 
    
    # Infrastructure Connections (Automatically matches SQLITE_URL, REDIS_URL, etc.)
    sqlite_url: str = "sqlite:///./devops_troubleshooter.db"
    redis_url: str = "redis://localhost:6379/0"
    
    # Ollama Local Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    
    # Security, Rate Limiting & Caching
    rate_limit_requests: int = 20
    rate_limit_window_sec: int = 60
    graphql_cache_ttl_sec: int = 300

    # Frontend/Client Configuration
    backend_url: str = "http://localhost:8000"

    @property
    def graphql_url(self) -> str:
        """Dynamically computes the GraphQL URL based on the current backend URL."""
        return f"{self.backend_url}/graphql"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"  # Ignores unmapped variables in the environment
    )

settings = Settings()