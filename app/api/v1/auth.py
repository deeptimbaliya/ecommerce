from fastapi import APIRouter, Query, Depends, Request
from sqlalchemy.orm import Session 
from app.schemas.user import  APIResponse,UserResponse, UserCreate
from app.schemas.auth import LoginRequest, PasswordResetConfirm, PasswordResetRequest, TokenResponse, RefreshTokenRequest
from app.services import auth
from app.core.database import get_db
from app.tasks.sendEmail import send_welcome_email
from app.core.celery_app import celery_app
from celery.result import AsyncResult
from app.core.logger import setup_logger
from app.core.rate_limiter import limiter

logger = setup_logger(__name__)


router= APIRouter(tags=["Auth"])

@router.post("/register", response_model=APIResponse,status_code=201)
@limiter.limit("3/minute")  
def register_user(request: Request, payload: UserCreate, db=Depends(get_db)):
    """Register a new user and return 201."""
    logger.info(f"Register endpoint called for email={payload.email}")
    new_user = auth.register_user(db, payload)
    send_welcome_email.delay(new_user.email,new_user.name)
    logger.info(f"Welcome email task queued for {new_user.email}")
    user_data = UserResponse.model_validate(new_user, from_attributes=True).model_dump()
    return APIResponse(success=True, message="User registered successfully", data=user_data)

@router.post("/login", response_model=TokenResponse,status_code=200)
@limiter.limit("5/minute")       
def login_user(request: Request, payload: LoginRequest, db=Depends(get_db)):
    """Authenticate a user and return a JWT token."""
    logger.info(f"Login endpoint called for email={payload.email}")
    token_data = auth.login_user(db, payload)
    return TokenResponse(**token_data)

@router.get("/task/{task_id}")
def get_task_status(task_id: str):
    """Get the status of a background task."""
    logger.debug(f"Checking task status: task_id={task_id}")
    task_result = celery_app.AsyncResult(task_id)
    return {"task_id": task_id, "status": task_result.status, "result": task_result.result}


@router.post("/forgot-password" )
@limiter.limit("3/hour") 
def forgot_password(request: Request, payload: PasswordResetRequest, db: Session = Depends(get_db)):
    logger.info(f"Forgot password endpoint called for email={payload.email}")
    return auth.forgot_password(db,payload.email)


@router.post("/reset-password")
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    logger.info("Reset password endpoint called")
    return auth.reset_password(db, payload)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute") 
def refresh_token(
    request: Request,
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Get new access token using refresh token."""
    return auth.refresh_access_token(db, payload.refresh_token)

@router.post("/logout")
def logout(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Logout — revokes the refresh token."""
    return auth.logout_user(db, payload.refresh_token)