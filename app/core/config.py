from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FP_", extra="ignore")

    database_url: str = "sqlite:///./app.db"
    mock_bank_base_url: str = "http://mock-bank:9000"
    reconciliation_window_days: int = 14


settings = Settings()
