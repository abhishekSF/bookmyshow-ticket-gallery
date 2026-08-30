"""Project settings from environment variables. Secrets stay in env or gitignored files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

SCRAPER_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRAPER_DIR.parent
DATA_DIR = SCRAPER_DIR / "data"
RAW_EMAIL_DIR = DATA_DIR / "raw_emails"
FILTERED_PATH = DATA_DIR / "filtered.json"
PARSED_PATH = DATA_DIR / "parsed.json"
ENRICHED_PATH = DATA_DIR / "enriched.json"
POSTERS_PATH = DATA_DIR / "with_posters.json"
DEFAULT_TICKETS_PATH = REPO_ROOT / "react-app" / "public" / "tickets.json"
DEFAULT_REVIEW_PATH = DATA_DIR / "review.json"
TABLEAU_CSV_PATH = DATA_DIR / "tableau.csv"
GMAIL_SCOPES = ("https://www.googleapis.com/auth/gmail.readonly",)


class Settings(BaseSettings):
    gmail_project_id: Optional[str] = None
    gmail_client_id: Optional[str] = None
    gmail_client_secret: Optional[str] = None
    gmail_token_file: str = str(REPO_ROOT / "tokens" / "gmail_token.json")
    gmail_credentials_file: str = str(REPO_ROOT / "tokens" / "gmail_credentials.json")
    gmail_enabled: bool = False

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_timeout_ms: int = 60000
    ollama_enable: bool = False

    tmdb_api_key: Optional[str] = None
    tmdb_enable: bool = True

    sf_url: str = "https://login.salesforce.com"
    sf_api_version: str = "v61.0"
    sf_client_id: Optional[str] = None
    sf_client_secret: Optional[str] = None
    sf_refresh_token: Optional[str] = None
    sf_tenant_id: Optional[str] = None
    sf_enabled: bool = Field(
        default=False, validation_alias=AliasChoices("SF_ENABLE", "SF_ENABLED")
    )
    sf_token_file: str = str(REPO_ROOT / "tokens" / "sf_tokens.json")
    sf_headless_360_url: str = (
        "https://api.salesforce.com/platform/mcp/v1/platform/headless-360"
    )

    tickets_json: str = str(DEFAULT_TICKETS_PATH)
    review_json: str = str(DEFAULT_REVIEW_PATH)
    app_name: str = "bookmyshow-ticket-gallery"

    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def tickets_path(self) -> Path:
        return Path(self.tickets_json)

    @property
    def review_path(self) -> Path:
        return Path(self.review_json)

    @property
    def gmail_readonly_scopes(self) -> tuple[str, ...]:
        return GMAIL_SCOPES


def ensure_data_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RAW_EMAIL_DIR.mkdir(parents=True, exist_ok=True)
    Path(os.path.dirname(settings.gmail_token_file) or ".").mkdir(
        parents=True, exist_ok=True
    )


settings = Settings()
ensure_data_dirs()
