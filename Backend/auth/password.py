# backend/auth/password.py

import bcrypt
import hashlib
import re


def _prepare_password(password: str) -> bytes:
    """
    Pre-hashes raw input with SHA-256 before handing to bcrypt.
    Bpasses bcrypt's 72-byte limit while preserving cryptographic entropy.
    """
    return hashlib.sha256(password.encode('utf-8')).digest()


def get_password_hash(password: str) -> str:
    """Generates a high-entropy bcrypt hash with work factor 12."""
    prepared = _prepare_password(password)
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(prepared, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Safely verifies plain password against stored bcrypt hash."""
    prepared = _prepare_password(plain_password)
    hashed_bytes = hashed_password.encode('utf-8')
    try:
        return bcrypt.checkpw(prepared, hashed_bytes)
    except Exception:
        return False


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validates enterprise password rules during registration."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    return True, ""