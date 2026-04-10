from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    finnhub_api_key: str = ""
    alpha_vantage_api_key: str = ""
    groq_api_key: str = ""

    app_env: str = "development"
    cache_ttl_seconds: int = 300
    prediction_lookback_days: int = 90
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    cors_allow_credentials: bool = False

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
