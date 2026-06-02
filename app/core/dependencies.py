from app.core.logger import setup_logger
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core import security
from app.core.database import get_db
from app.models.user import User

logger = setup_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme))-> User:
    logger.debug("Authenticating user from token")
    token_data = security.decode_access_token(token)
    if not token_data:
        logger.warning("Authentication failed — invalid token")
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == token_data.get("sub")).first()
    if not user:
        logger.warning(f"Authentication failed — user id={token_data.get('sub')} not found")
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        logger.warning(f"Authentication failed — user id={user.id} is deactivated")
        raise HTTPException(status_code=403, detail="Account is deactivated")
    logger.debug(f"Authenticated user: id={user.id}, role={user.role}")
    return user

def is_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        logger.warning(f"Admin access denied for user id={current_user.id}, role={current_user.role}")
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user



