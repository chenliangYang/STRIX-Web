"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_env: str = "development"
    app_name: str = "STRIX Web"
    api_prefix: str = "/api"

    # Database
    database_url: str = "mysql+pymysql://strix_user:change_me@localhost:3306/strix_web?charset=utf8mb4"

    # Redis
    redis_url: str = "redis://:change_me@localhost:6379/0"

    # JWT
    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 1440

    # STRIX
    strix_bin: str = "strix"
    strix_base_workdir: str = "./storage/runs"
    strix_default_timeout_seconds: int = 7200
    strix_event_poll_interval_ms: int = 500
    strix_max_concurrent_runs: int = 2

    # Runner
    runner_mode: str = "in_process"
    runner_node_id: str = "local-dev"
    task_queue_backend: str = "in_memory"
    lock_backend: str = "redis"
    event_bus_backend: str = "redis"

    # Storage
    artifact_retention_days: int = 30

    # Logging
    log_level: str = "INFO"

    @property
    def base_dir(self) -> Path:
        """Get base directory."""
        return Path(__file__).parent.parent.parent

    @property
    def storage_dir(self) -> Path:
        """Get storage directory."""
        return self.base_dir / "storage"

    @property
    def runs_dir(self) -> Path:
        """Get runs directory."""
        return self.storage_dir / "runs"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings."""
    return Settings()
