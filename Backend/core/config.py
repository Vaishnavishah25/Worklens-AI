import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Dynamic Path Detection: Locate .env explicitly relative to this file's position
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(CURRENT_DIR)
ENV_PATH = os.path.join(BACKEND_ROOT, ".env")

# Stream secrets directly into active process memory (safe from shell command logs)
if os.path.exists(ENV_PATH):
    load_dotenv(dotenv_path=ENV_PATH)
else:
    # Optional: Fallback check if your .env is sitting at the absolute project root workspace level
    WORKSPACE_ROOT = os.path.dirname(BACKEND_ROOT)
    WORKSPACE_ENV_PATH = os.path.join(WORKSPACE_ROOT, ".env")
    if os.path.exists(WORKSPACE_ENV_PATH):
        load_dotenv(dotenv_path=WORKSPACE_ENV_PATH)

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    
    # Secure Pydantic settings loading configuration
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8", 
        extra="ignore"  # Gracefully ignores extra ecosystem keys like OpenAI tokens
    )

# Instantiates and validates the settings against securely injected process memory
settings = Settings()