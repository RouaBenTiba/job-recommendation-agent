from sqlalchemy.orm import Session

from app.core.security import TokenPayload
from app.models.revoked_token import RevokedToken


def is_revoked(db: Session, jti: str) -> bool:
    return db.get(RevokedToken, jti) is not None


def revoke(db: Session, payload: TokenPayload) -> None:
    """Idempotent: revoking an already revoked token is a no-op."""
    if not is_revoked(db, payload.jti):
        db.add(RevokedToken(jti=payload.jti, expires_at=payload.exp))
        db.commit()
