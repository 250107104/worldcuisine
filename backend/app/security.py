"""Password hashing and JWT helpers for account authentication."""
import os
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

_password_hash = PasswordHash.recommended()
# Run the password hash even for unknown accounts to reduce email-enumeration timing differences.
_DUMMY_PASSWORD_HASH = _password_hash.hash("dummy-password-never-used-for-login")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)


def hash_password(password: str) -> str:
    """Return a salted Argon2id hash; callers must never persist the input."""
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its encoded hash."""
    return _password_hash.verify(password, password_hash)


def verify_password_or_dummy(password: str, password_hash: str | None) -> bool:
    """Verify against a dummy hash for accounts without usable credentials."""
    return verify_password(password, password_hash or _DUMMY_PASSWORD_HASH) and password_hash is not None


def create_access_token(subject: str) -> tuple[str, int]:
    """Create a short-lived signed JWT. Configure JWT_SECRET_KEY with a random secret."""
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret or len(secret.encode("utf-8")) < 32:
        raise RuntimeError("Set JWT_SECRET_KEY to a secret of at least 32 bytes")
    now = datetime.now(timezone.utc)
    expires_at = now + ACCESS_TOKEN_LIFETIME
    payload = {"sub": subject, "iat": now, "exp": expires_at}
    token = jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)
    return token, int(ACCESS_TOKEN_LIFETIME.total_seconds())


def decode_access_token(token: str) -> dict:
    """Decode and validate an access token, raising PyJWT errors if invalid."""
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret or len(secret.encode("utf-8")) < 32:
        raise RuntimeError("Set JWT_SECRET_KEY to a secret of at least 32 bytes")
    return jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
