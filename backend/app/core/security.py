"""
Security & Cryptography Utilities
Argon2id password hashing, constant-time comparison, and secure session tokens.
"""
import hashlib
import secrets
from passlib.context import CryptContext
from backend.app.core.errors import ValidationException

# Primary Argon2id password hasher with bcrypt fallback capability
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    if len(password) < 8:
        raise ValidationException("Password must be at least 8 characters long")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def generate_secure_token(nbytes: int = 32) -> str:
    """Generates a cryptographically strong URL-safe random string."""
    return secrets.token_urlsafe(nbytes)


def hash_session_token(token: str) -> str:
    """Hashes session token before database persistence to prevent plaintext session exposure."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
