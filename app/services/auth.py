from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.logger import setup_logger
from app.schemas import auth as auth_schemas
from app.schemas import user as user_schemas
from app.models.user import User
from app.core import security
from app.core.config import settings
from app.models.refresh_token import RefreshToken
from app.tasks.sendEmail import send_password_reset_email
import secrets
from datetime import datetime, timedelta, timezone

logger = setup_logger(__name__) 

# NOTE: In production, store tokens in Redis with TTL instead of in-memory dict
reset_tokens: dict = {}


def register_user(db: Session, payload: user_schemas.UserCreate) -> User:
    """Register a new user and return the created user."""
    logger.info(f"Registration attempt for email={payload.email}")
    # Check for duplicate email
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        logger.warning(f"Registration failed — duplicate email: {payload.email}")
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    new_user = User(
        name=payload.name,
        email=payload.email,
        password_hash=security.hash_password(payload.password),
        role="user",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"User registered successfully: id={new_user.id}, email={new_user.email}")
    return new_user


def login_user(db: Session, payload: auth_schemas.LoginRequest) -> User:
    """Authenticate a user and return the user object if valid."""
    logger.info(f"Login attempt for email={payload.email}")
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not security.verify_password(payload.password, user.password_hash):
        logger.warning(f"Login failed — invalid credentials for email={payload.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        logger.warning(f"Login failed — account deactivated for user id={user.id}")
        raise HTTPException(status_code=403, detail="Account is deactivated")
    token_data = {"sub": str(user.id), "role": user.role}
    access_token = security.create_access_token(token_data)
    refresh_token = security.create_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    db_token = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=expires_at
    )
    db.add(db_token)
    db.commit()
    logger.info(f"Login successful for user id={user.id}")
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


def forgot_password(db: Session, email: str):
    """Handle forgot password logic (to be implemented)."""
    logger.info(f"Password reset requested for email={email}")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.warning(f"Password reset — no account found for email={email}")
        return {"message": "If an account with that email exists, a password reset link has been sent."}
    
    token = secrets.token_urlsafe(32)

    expires_in = datetime.now(timezone.utc) + timedelta(minutes=30)
    reset_tokens[token] = {"user_id": user.id, "expires_at": expires_in}

    send_password_reset_email.delay(user.email, user.name, token)  # Placeholder for sending reset email with token
    logger.info(f"Password reset email queued for user id={user.id}")


    

    return {"message": "If that email exists, a reset link has been sent"}


def reset_password(db: Session, payload: auth_schemas.PasswordResetConfirm):
    """Handle password reset logic (to be implemented)."""
    logger.info("Password reset confirmation attempt")
    token_data = reset_tokens.get(payload.token)
    if not token_data:
        logger.warning("Password reset failed — invalid token")
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    if datetime.now(timezone.utc) > token_data["expires_at"]:
        logger.warning("Password reset failed — token expired")
        del reset_tokens[payload.token]
        raise HTTPException(status_code=400, detail="Token has expired")

    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user:
        logger.warning(f"Password reset failed — user id={token_data['user_id']} not found")
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = security.hash_password(payload.new_password)
    db.commit()
    del reset_tokens[payload.token]
    logger.info(f"Password reset successful for user id={user.id}")
    return {"message": "Password has been reset successfully"}


def refresh_access_token(db: Session, refresh_token: str) -> dict:
    """Validate refresh token, rotate it, return new token pair."""
    logger.info("Token refresh attempt")

    # Find token in DB
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token
    ).first()

    # Token not found
    if not db_token:
        logger.warning("Refresh failed — token not found")
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Token already revoked — REUSE DETECTED!
    if db_token.is_revoked:
        logger.warning(f"Refresh token reuse detected! user_id={db_token.user_id}")
        # Revoke ALL tokens for this user — security breach
        db.query(RefreshToken).filter(
            RefreshToken.user_id == db_token.user_id
        ).update({"is_revoked": True})
        db.commit()
        raise HTTPException(status_code=401, detail="Token reuse detected. Please login again.")

    # Token expired
    token_expiry = db_token.expires_at.replace(tzinfo=timezone.utc) if db_token.expires_at.tzinfo is None else db_token.expires_at
    if datetime.now(timezone.utc) > token_expiry:
        logger.warning(f"Expired refresh token used: user_id={db_token.user_id}")
        db_token.is_revoked = True
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token expired. Please login again.")

    # ✅ Valid — rotate the token
    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or deactivated")

    # Revoke OLD token
    db_token.is_revoked = True

    # Create NEW token pair
    new_access_token = security.create_access_token({"sub": str(user.id), "role": user.role})
    new_refresh_token = security.create_refresh_token()

    new_db_token = RefreshToken(
        token=new_refresh_token,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    )
    db.add(new_db_token)
    db.commit()

    logger.info(f"Token rotated successfully: user_id={user.id}")
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


def logout_user(db: Session, refresh_token: str) -> dict:
    """Revoke the refresh token on logout."""
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token
    ).first()

    if db_token:
        db_token.is_revoked = True
        db.commit()
        logger.info(f"User logged out: user_id={db_token.user_id}")

    return {"message": "Logged out successfully"}
