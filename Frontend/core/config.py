from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]
ROOT_ENV = ROOT_DIR/".env"



class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    API_BASE_URL:str = "http://localhost:8000/api/v1"

    model_config = SettingsConfigDict(
        env_file=ROOT_ENV,
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
