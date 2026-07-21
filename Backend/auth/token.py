# backend/auth/token.py

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from core.config import settings

# Enforce secure secret key resolution
SECRET_KEY = getattr(settings, "JWT_SECRET_KEY", getattr(settings, "JWT_SECRET", None)) or os.getenv("JWT_SECRET_KEY")

if not SECRET_KEY or SECRET_KEY in ("worklens_default_secret", "your-secret-key", "change_this_secret"):
    if os.getenv("ENVIRONMENT", "development").lower() == "production":
        raise RuntimeError("CRITICAL SECURITY RISK: Insecure or default JWT_SECRET_KEY detected in production!")
    SECRET_KEY = "worklens_dev_only_secret_change_in_production"

ALGORITHM = getattr(settings, "JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Short-lived access token
REFRESH_TOKEN_EXPIRE_DAYS = 7     # Long-lived refresh token


def create_access_token(user_id: int, email: str, role: str, team_id: Optional[int] = None) -> str:
    """Generates a short-lived access token scoped for API authorization."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email.lower().strip(),
        "role": role.lower().strip(),
        "team_id": team_id,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int, email: str) -> str:
    """Generates a long-lived refresh token strictly for token renewal."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "email": email.lower().strip(),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str, expected_type: str = "access") -> Optional[dict]:
    """Cryptographically verifies token signature, expiration, and intended scope."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload
    except JWTError:
        return None