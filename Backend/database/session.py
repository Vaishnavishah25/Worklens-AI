from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from app.core.config import settings
except ModuleNotFoundError:
    from core.config import settings


APP_DIR = Path(__file__).resolve().parents[1]
SQLITE_URL = f"sqlite:///{(APP_DIR / 'worklens.db').as_posix()}"


def _resolve_database_url() -> str:
    database_url = getattr(settings, "DATABASE_URL", "sqlite:///./worklens.db")
    if database_url.startswith(("postgresql", "postgres")):
        return SQLITE_URL
    if database_url == "sqlite:///./worklens.db":
        return SQLITE_URL
    return database_url


database_url = _resolve_database_url()
engine_kwargs = {"echo": False}
if database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {
        "check_same_thread": False,
        "timeout": 30,
    }

engine = create_engine(database_url, **engine_kwargs)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False
)
