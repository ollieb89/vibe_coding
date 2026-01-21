"""Configuration management using Pydantic settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="CORPUS_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Database
    database_path: Path = Path("corpus.sqlite")

    # Ollama settings
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "mistral"

    # Analysis settings
    chunk_size: int = 1000
    chunk_overlap: int = 100

    # Output
    reports_dir: Path = Path("reports")
    templates_dir: Path = Path("templates")


settings = Settings()
