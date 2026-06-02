from pydantic import BaseModel, EmailStr
from pydantic import Field, field_validator, model_validator, computed_field
from typing import List, Optional, Any  # ✅ added Any


class UserCreate(BaseModel):
    model_config = {"str_strip_whitespace": True}

    name: str = Field(..., min_length=2, max_length=50)       
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    role: str = Field("user", pattern="^(user|admin)$")  

    @field_validator("name")
    @classmethod
    def validate_name(cls, values):
        if any(c.isdigit() for c in values):
            raise ValueError("Name cannot contain numbers")
        return values.title()

    @field_validator("password")
    @classmethod
    def validate_password(cls, values):
        if not any(c.isupper() for c in values):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in values):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in values):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:'\",.<>/?`~" for c in values):
            raise ValueError("Password must contain at least one special character")
        return values
    
    @field_validator("role")
    @classmethod
    def validate_role(cls, values):
        if values not in ["user", "admin"]:
            raise ValueError("Invalid role")
        return values

    @model_validator(mode="after")
    def validate_passwords_match(self) -> "UserCreate":
        if self.password != self.confirm_password:             
            raise ValueError("Passwords do not match")
        return self


class UserUpdate(BaseModel):
    model_config = {"str_strip_whitespace": True}

    name: Optional[str] = Field(None, min_length=2, max_length=50)  
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    confirm_password: Optional[str] = Field(None, min_length=8, max_length=128)
    role: Optional[str] = Field(None, pattern="^(user|admin)$")
    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, values):
        if values is None:
            return values
        if any(c.isdigit() for c in values):
            raise ValueError("Name cannot contain numbers")
        return values.title()

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, values):
        if values is None:
            return values
        if not any(c.isupper() for c in values):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in values):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in values):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:'\",.<>/?`~" for c in values):
            raise ValueError("Password must contain at least one special character")
        return values


class UserResponse(BaseModel):
    model_config = {"from_attributes": True} 
    id: int
    name: str
    email: str
    role: str
    avatar_url: Optional[str] = None
    is_active: bool

    @computed_field
    @property
    def display_name(self) -> str:
        return f"User #{self.id} — {self.name}"


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None              