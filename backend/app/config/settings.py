from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    app_name: str = "EasyFill"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_cors_origins: list[str] = ["*"]

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "easyfill"
    postgres_user: str = "easyfill"
    postgres_password: str = "easyfill_dev_password"

    model_provider: str = "ollama"
    model_name: str = "gpt-4o"
    openai_api_key: Optional[str] = None

    fallback_provider: str = "anthropic"
    fallback_model: str = "claude-sonnet-4-20250514"
    anthropic_api_key: Optional[str] = None

    second_fallback_provider: str = "google"
    second_fallback_model: str = "gemini-2.0-flash"
    google_api_key: Optional[str] = None

    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "anthropic/claude-sonnet-4"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:7b"

    bedrock_region: str = "us-east-1"
    bedrock_model: str = "anthropic.claude-sonnet-4-20250514-v1:0"
    bedrock_access_key_id: Optional[str] = None
    bedrock_secret_access_key: Optional[str] = None
    bedrock_session_token: Optional[str] = None
    bedrock_profile: Optional[str] = None

    model_timeout: int = 120
    model_max_retries: int = 3

    embedding_backend: str = "ollama"  # "ollama" or "onnx"
    embedding_model: str = "nomic-embed-text"
    onnx_embedding_model: str = "nomic-ai/nomic-embed-text-v1.5"

    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    model_config = {
        "env_file": str(ENV_FILE),
        "env_file_encoding": "utf-8",
        "protected_namespaces": ("settings_",),
        "extra": "ignore",
    }


settings = Settings()
