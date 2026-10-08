from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings  # ADAPTER à ton Settings


def get_database_url() -> str:
    url = get_settings().database_url  # ADAPTER (SecretStr : .get_secret_value())
    # Les URL « postgresql:// » utiliseraient psycopg2 : on force le pilote psycopg 3.
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    with SessionLocal() as db:
        yield db