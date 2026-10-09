import app.models  # noqa: F401
from app.db.base import Base

EXPECTED_TABLES = {
    "users",
    "cvs",
    "candidate_profiles",
    "preferences",
    "job_offers",
    "searches",
    "recommendations",
    "revoked_tokens",
}


def test_all_tables_are_registered() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_unique_columns() -> None:
    tables = Base.metadata.tables
    assert tables["users"].c.email.unique
    assert tables["preferences"].c.user_id.unique
    assert tables["job_offers"].c.content_hash.unique


def test_delete_rules() -> None:
    tables = Base.metadata.tables
    cv_fk = next(iter(tables["cvs"].c.user_id.foreign_keys))
    offer_fk = next(iter(tables["recommendations"].c.job_offer_id.foreign_keys))
    assert cv_fk.ondelete == "CASCADE"
    assert offer_fk.ondelete == "RESTRICT"
