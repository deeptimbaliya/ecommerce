import hashlib
import secrets
import bcrypt
from fastapi import HTTPException
from jose import JWTError, jwt
from datetime import datetime, timedelta,timezone
from app.core.config import settings
import base64



def _pre_hash(password: str) -> str:
    """SHA256 the password first to avoid bcrypt 72-byte limit."""
    return base64.b64encode(
        hashlib.sha256(password.encode("utf-8")).digest()
    )

def hash_password(password: str) -> str:
    """Hash a plaintext password."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(_pre_hash(password), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hashed password."""
    return bcrypt.checkpw(_pre_hash(plain_password), hashed_password.encode("utf-8"))

def create_refresh_token() -> str:
    """Generate a secure random string for refresh token."""
    return secrets.token_urlsafe(64)


def create_access_token(data: dict) -> str:
    """Create a JWT access token with an expiration."""
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> dict:
    """Decode a JWT access token and return the payload, or raise 401."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
     