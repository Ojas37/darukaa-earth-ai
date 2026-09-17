import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    app_name: str = "Darukaa.Earth AI Biodiversity Intelligence"
    app_version: str = "0.1.0"
    environment: str = Field(default="development")
    anthropic_api_key: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022")
    database_url: str = Field(default="sqlite+aiosqlite:///./daruka.db")
    chroma_db_dir: str = Field(default="./data/knowledge/chroma")
    log_level: str = Field(default="INFO")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
