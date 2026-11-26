"""Password hashing helpers for user credentials."""
from pwdlib import PasswordHash


_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Return a salted Argon2id hash; callers must never persist the input."""
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its encoded hash."""
    return _password_hash.verify(password, password_hash)
