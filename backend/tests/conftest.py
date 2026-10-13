import os
import uuid
from collections.abc import Iterator

# Fake values set before the app is imported: no real secret is ever used in tests.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("GEMINI_API_KEY", "fake-gemini-key")
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-32-bytes!")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import Engine, create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

import app.models  # noqa: E402,F401  (registers every table on Base.metadata)
from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_database_url, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini-key")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-with-at-least-32-bytes!")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    # PostgreSQL is required (JSONB, ARRAY, partial indexes): CI provides a service,
    # locally use TEST_DATABASE_URL or the DATABASE_URL default above.
    url = os.getenv("TEST_DATABASE_URL") or get_database_url()
    test_engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.create_all(test_engine)  # no-op for tables Alembic already created
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Iterator[Session]:
    """Each test runs in a transaction that is rolled back: the database stays clean."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    """Crée un compte, se connecte et renvoie l'en-tête d'authentification."""
    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    password = "Motdepasse123!"

    register = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert register.status_code in (200, 201), register.text

    # Version « formulaire OAuth2 » (champs username et password)
    login = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    # Si le résultat de l'étape 1 était 'application/json', remplace par :
    # login = client.post(
    #     "/api/v1/auth/login", json={"email": email, "password": password}
    # )
    assert login.status_code == 200, login.text

    return {"Authorization": f"Bearer {login.json()['access_token']}"}
