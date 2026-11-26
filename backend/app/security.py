"""Password hashing and JWT helpers for account authentication."""
import os
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

_password_hash = PasswordHash.recommended()
_DUMMY_PASSWORD_HASH = _password_hash.hash("dummy-password-never-used-for-login")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret or len(secret.encode("utf-8")) < 32:
        raise RuntimeError("Set JWT_SECRET_KEY to a secret of at least 32 bytes")
    return secret


def hash_password(password: str) -> str:
    """Return a salted Argon2id hash; callers must never persist the input."""
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its encoded hash."""
    return _password_hash.verify(password, password_hash)


def verify_password_or_dummy(password: str, password_hash: str | None) -> bool:
    """Verify against a dummy hash for accounts without usable credentials."""
    valid = verify_password(password, password_hash or _DUMMY_PASSWORD_HASH)
    return valid and password_hash is not None


def create_access_token(subject: str) -> tuple[str, int]:
    """Create a signed, short-lived JWT access token."""
    now = datetime.now(timezone.utc)
    lifetime = int(ACCESS_TOKEN_LIFETIME.total_seconds())
    token = jwt.encode(
        {"sub": subject, "iat": now, "exp": now + ACCESS_TOKEN_LIFETIME},
        _jwt_secret(), algorithm=JWT_ALGORITHM,
    )
    return token, lifetime


def decode_access_token(token: str) -> dict:
    """Validate and decode an access token."""
    return jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
