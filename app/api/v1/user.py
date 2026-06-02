from fastapi import APIRouter, Query, Depends, UploadFile
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, APIResponse, UserUpdate
from app.services import user_service
from app.services import upload_service
from app.core.database import get_db
from app.core.dependencies import get_current_user, is_admin


router = APIRouter(tags=["Users"])


@router.get("/users", response_model=APIResponse)
async def get_users(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    _ : User = Depends(is_admin)
):
    """Return a paginated list of users."""
    data = await user_service.list_users_cached(db, page, limit)
    # Convert ORM objects to serializable dicts
    data["users"] = [UserResponse.model_validate(u, from_attributes=True).model_dump() for u in data["users"]]
    return APIResponse(success=True, message="Users fetched successfully", data=data)


@router.get("/users/me", response_model=APIResponse)
def get_current_user(
    current_user: User = Depends(get_current_user)
):
    """Return the currently authenticated user's information."""
    user_data = UserResponse.model_validate(current_user, from_attributes=True)
    return APIResponse(success=True, message="Current user fetched successfully", data=user_data)



@router.get("/users/{user_id}", response_model=APIResponse)
async def get_user(
    user_id: int, 
    db: Session = Depends(get_db),
    _: User = Depends(is_admin)
    ):
    """Return a single user by ID."""
    user = await user_service.get_user_cached(db, user_id)
    user_data = UserResponse.model_validate(user, from_attributes=True).model_dump()
    return APIResponse(success=True, message="User fetched successfully", data=user_data)


@router.post("/users", response_model=APIResponse, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(is_admin)
):
    """Create a new user and return 201."""
    new_user = user_service.create_user(db, payload)
    user_data = UserResponse.model_validate(new_user, from_attributes=True).model_dump()
    return APIResponse(success=True, message="User created successfully", data=user_data)

@router.put("/users/{user_id}", response_model=APIResponse)
def update_user(
    user_id: int, 
    payload: UserUpdate, 
    db: Session = Depends(get_db),
    _: User = Depends(is_admin)
):
    """Update an existing user and return the updated data."""
    # For simplicity, we'll reuse the create_user logic here.
    # In a real app, you'd want a separate update function that handles partial updates.
    updated_user = user_service.update_user(db, user_id, payload)
    user_data = UserResponse.model_validate(updated_user, from_attributes=True).model_dump()
    return APIResponse(success=True, message="User updated successfully", data=user_data)


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int, 
    db: Session = Depends(get_db),
    _: User = Depends(is_admin)
):
    """Delete a user and return 204 No Content."""
    user_service.delete_user(db, user_id)
    # 204 responses must have no body
    return None

@router.post("/users/setavatar", response_model=APIResponse)
async def set_profile_avatar(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.avatar_url:
        old_public_id = f"ecommerce/avatar/{current_user.id}/avatar_{current_user.id}"
        await upload_service.delete_profile_avatar(old_public_id)
    """Set or update a user's profile avatar."""
    avatar_data = await upload_service.upload_profile_avatar(file, current_user.id)


    current_user.avatar_url = avatar_data["url"]
    db.commit()

    return APIResponse(success=True, message="Profile avatar updated successfully", data=avatar_data)
