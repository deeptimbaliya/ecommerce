"""
Business logic for user operations.
All data manipulation happens here — the router stays thin.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session 
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core import security
from app.core.logger import setup_logger
from app.core.cache import delete_cache, delete_pattern, get_cache, set_cache, CacheTTL

logger = setup_logger(__name__) 

def list_users(db: Session, page: int, limit: int) -> dict:
    """Return a paginated slice of users."""
    logger.info(f"Fetching users — page={page}, limit={limit}")
    total = db.query(User).count()
    start = (page - 1) * limit
    paginated = db.query(User).offset(start).limit(limit).all()
    total_pages = (total + limit - 1) // limit  # Ceiling division for total pages
    logger.debug(f"Found {total} users, returning page {page}/{total_pages}")

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "users": paginated,
    }

async def list_users_cached(db: Session, page: int, limit: int) -> dict:
    """List users with Redis caching."""
    cache_key = f"users:list:page:{page}:limit:{limit}"

    cached = await get_cache(cache_key)
    if cached:
        return cached   

    result = list_users(db, page, limit)

    # 3. Store in cache for 5 minutes
    await set_cache(cache_key, result, ttl=CacheTTL.MEDIUM)

    return result

async def get_user_cached(db: Session, user_id: int) -> dict:
    """Get single user with caching."""
    cache_key = f"users:{user_id}"

    cached = await get_cache(cache_key)
    if cached:
        return cached

    user = get_user_by_id(db, user_id)
    user_data = {"id": user.id, "name": user.name, "email": user.email}
    await set_cache(cache_key, user_data, ttl=CacheTTL.LONG)

    return user_data

def get_user_by_id(db: Session, user_id: int) -> User:
    """Return a single user by ID, or raise 404."""
    logger.info(f"Fetching user by id={user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User with id={user_id} not found")
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    logger.debug(f"Found user: id={user.id}, email={user.email}")
    return user


def create_user(db: Session, payload: UserCreate) -> User:
    """Validate uniqueness, create, and return the new user."""
    logger.info(f"Creating user with email={payload.email}")
    # Check for duplicate email
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        logger.warning(f"Duplicate email rejected: {payload.email}")
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    new_user = User(
        name=payload.name,
        email=payload.email,
        password_hash=security.hash_password(payload.password),
        role=payload.role 
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"User created successfully: id={new_user.id}, email={new_user.email}")
    return new_user

async def delete_user_cached(db: Session, user_id: int) -> None:
    """Delete user and invalidate cache."""
    delete_user(db, user_id)

    # ✅ Invalidate cache
    await delete_cache(f"users:{user_id}")
    await delete_pattern("users:list:*")

def delete_user(db: Session, user_id: int) -> None:
    """Delete a user by ID, or raise 404."""
    logger.info(f"Deleting user with id={user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"Delete failed — user with id={user_id} not found")
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    db.delete(user)
    db.commit()
    logger.info(f"User deleted successfully: id={user_id}")


async def update_user_cached(db: Session, user_id: int, payload: UserUpdate) -> User:
    """Update user and invalidate cache."""
    user = update_user(db, user_id, payload)

    # ✅ Delete affected cache keys
    await delete_cache(f"users:{user_id}")        # single user cache
    await delete_pattern("users:list:*")          # all list caches

    return user



def update_user(db: Session, user_id: int, payload: UserUpdate) -> User:
    """Update an existing user, or raise 404."""
    logger.info(f"Updating user with id={user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"Update failed — user with id={user_id} not found")
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")

    # Check for duplicate email (excluding current user)
    existing_user = db.query(User).filter(User.email == payload.email, User.id != user_id).first()
    if existing_user:
        logger.warning(f"Update failed — duplicate email: {payload.email}")
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    if payload.name is not None:
        user.name = payload.name
    if payload.email is not None:
        user.email = payload.email
    if payload.password is not None:
        user.password_hash = security.hash_password(payload.password)
    if payload.role is not None:
        user.role = payload.role

    db.commit()
    db.refresh(user)
    logger.info(f"User updated successfully: id={user_id}")
    return user