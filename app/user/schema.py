from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional
from fastapi import status

from ..auth.schema import INVALID_OR_EXPIRED_TOKEN
from ..user.models import UserType, UserStatus
from ..core.utils import trim_and_reject_blank

# Models Schemas
class UserBase(BaseModel):
    full_name: str = Field(min_length=1, description="The full name of the user")
    user_code: str = Field(min_length=1, description="The user code of the user")
    user_type: UserType = Field(default=UserType.HUMAN, description="The type of the user")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="The status of the user")
    # roles_assigned: Optional[list[str]] = Field(default=[], description="The codes of the roles assigned to the user")


    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, v: str) -> str:
        return trim_and_reject_blank(v)

    @field_validator("user_code", mode="before")
    @classmethod
    def normalize_user_code(cls, v: str) -> str:
        return trim_and_reject_blank(v).upper()


class UserCreateRequest(UserBase):
    password: Optional[str] = Field(min_length=8, max_length=100, default=None, description="The password of the user")

class UserCreate(UserCreateRequest):
    created_by_id: Optional[int] = Field(default=None, description="The ID of the user who created the user")
    
class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(min_length=1, max_length=200, default=None, description="The full name of the user")
    user_type: Optional[UserType] = Field(default=None, description="The type of the user")
    status: Optional[UserStatus] = Field(default=None, description="The status of the user")
    password: Optional[str] = Field(min_length=8, max_length=100, default=None, description="The password of the user")

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return trim_and_reject_blank(v)
    

class UserUpdate(UserUpdateRequest):
    updated_by_id: int = Field(description="The ID of the user who updated the user")
    deleted_by_id: Optional[int] = Field(default=None, description="The ID of the user who deleted the user")
    deleted_at: Optional[datetime] = Field(default=None, description="The date and time the user was deleted")

class UserResponse(UserBase):
    id: int
    created_at: datetime = Field(description="The date and time the user was created")
    created_by_id: Optional[int] = Field(default=None, description="The ID of the user who created the user")
    updated_at: Optional[datetime] = Field(default=None, description="The date and time the user was updated")
    updated_by_id: Optional[int] = Field(default=None, description="The ID of the user who updated the user")
    deleted_at: Optional[datetime] = Field(default=None, description="The date and time the user was deleted")
    deleted_by_id: Optional[int] = Field(default=None, description="The ID of the user who deleted the user")
    role_codes: list[dict] = Field(default_factory=list, description="The codes of the roles assigned to the user")
    model_config = ConfigDict(from_attributes=True) # this allows us to access attributes by dot notation like user.id instead of user["id"]


# API Responses Schemas
USER400 = {status.HTTP_400_BAD_REQUEST: {"description": "User with user code already exists"}}
USER403 = {status.HTTP_403_FORBIDDEN: {"description": "You are not allowed to update/delete this user"}}
USER404 = {status.HTTP_404_NOT_FOUND: {"description": "User not found"}}
USERPATCHDELETE = {**INVALID_OR_EXPIRED_TOKEN, **USER400, **USER403, **USER404}