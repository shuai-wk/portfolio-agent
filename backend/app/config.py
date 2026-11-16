from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/portfolio"
    embedding_dim: int = 4
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = ""
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_api_key: str = ""
    embedding_model: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()

