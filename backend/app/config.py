import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv

# Search for .env in current directory, backend directory, and project root
_backend_dir = Path(__file__).resolve().parent.parent
_root_dir = _backend_dir.parent

for _p in [Path.cwd() / ".env", _backend_dir / ".env", _root_dir / ".env"]:
    if _p.is_file():
        load_dotenv(_p, override=False)

class Settings(BaseSettings):
    app_name: str = "Darukaa.Earth AI Biodiversity Intelligence"
    app_version: str = "0.1.0"
    environment: str = Field(default="development")
    anthropic_api_key: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022")
    groq_api_key: str = Field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    database_url: str = Field(default="sqlite+aiosqlite:///./daruka.db")
    chroma_db_dir: str = Field(default="./data/knowledge/chroma")
    log_level: str = Field(default="INFO")

    model_config = SettingsConfigDict(
        env_file=str(_backend_dir / ".env"),
        extra="ignore"
    )

settings = Settings()
