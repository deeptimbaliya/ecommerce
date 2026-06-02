from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User


def register_user(db: Session, payload) -> User:
    """Register a new user and return the created user."""
    # Check for duplicate email
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    new_user = User(
        name=payload.name,
        email=payload.email,
        password_hash=payload.password,  # In production, hash this!
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
