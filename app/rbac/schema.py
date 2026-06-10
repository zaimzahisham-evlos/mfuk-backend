from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from datetime import datetime
from typing import Optional
from app.core.utils import trim_and_reject_blank, utcnow
from app.rbac.models import *
from app.user.models import UserStatus

# Models Schemas

class PartialSuccessResponse(BaseModel):
    requested_count: int
    assigned_count: int 
    revoked_count: int 
    skipped_count: int 

# Permissions Schemas
class PermissionBase(BaseModel):
    permission_code: str = Field(min_length=3, max_length=80, description="The code of the permission", pattern=r"^[A-Z0-9_]+$")
    permission_name: str = Field(min_length=1, description="The name of the permission")
    module: str = Field(min_length=1, description="The module of the permission")
    category: PermissionCategory = Field(default=PermissionCategory.VIEW, description="The category of the permission")
    is_system_permission: bool = Field(default=False, description="Whether the permission is a system permission")
    status: PermissionStatus = Field(default=PermissionStatus.ACTIVE, description="The status of the permission")
    description: Optional[str] = Field(default=None, description="The description of the permission")

    @field_validator("permission_code", mode="before")
    @classmethod
    def normalize_permission_code(cls, v: str) -> str:
        return trim_and_reject_blank(v).upper()

    @field_validator("module", mode="before")
    @classmethod
    def normalize_module(cls, v: str) -> str:
        return trim_and_reject_blank(v).title()

    @field_validator("permission_name", mode="before")
    @classmethod
    def normalize_permission_name(cls, v: str) -> str:
        return trim_and_reject_blank(v)

class PermissionCreateRequest(PermissionBase):
    description: Optional[str] = Field(default=None, description="The description of the permission")

class PermissionCreate(PermissionCreateRequest):
    created_by_id: Optional[int] = Field(default=None, description="The ID of the user who created the permission")

class PermissionUpdateRequest(BaseModel):
    permission_name: Optional[str] = Field(min_length=1, max_length=200, default=None, description="The name of the permission")
    module: Optional[str] = Field(min_length=1, max_length=200, default=None, description="The module of the permission")
    category: Optional[PermissionCategory] = Field(default=None, description="The category of the permission")
    status: Optional[PermissionStatus] = Field(default=None, description="The status of the permission")
    description: Optional[str] = Field(default=None, description="The description of the permission")

    @field_validator("module", mode="before")
    @classmethod
    def normalize_module(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return trim_and_reject_blank(v).title()
    
    @field_validator("permission_name", mode="before")
    @classmethod
    def normalize_permission_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return trim_and_reject_blank(v)


class PermissionUpdate(PermissionUpdateRequest):
    updated_by_id: Optional[int] = Field(default=None, description="The ID of the user who updated the permission")
    deleted_by_id: Optional[int] = Field(default=None, description="The ID of the user who deleted the permission")
    deleted_at: Optional[datetime] = Field(default=None, description="The date and time the permission was deleted")

class PermissionResponse(PermissionBase):
    id: int
    created_at: datetime = Field(description="The date and time the permission was created")
    created_by_id: Optional[int] = Field(default=None, description="The ID of the user who created the permission")
    updated_at: Optional[datetime] = Field(default=None, description="The date and time the permission was updated")
    updated_by_id: Optional[int] = Field(default=None, description="The ID of the user who updated the permission")
    deleted_at: Optional[datetime] = Field(default=None, description="The date and time the permission was deleted")
    deleted_by_id: Optional[int] = Field(default=None, description="The ID of the user who deleted the permission")
    model_config = ConfigDict(from_attributes=True) # this allows us to access attributes by dot notation like permission.id instead of permission["id"]


# Roles Schemas
class RoleBase(BaseModel):
    role_code: str = Field(min_length=3, max_length=80, description="The code of the role", pattern=r"^[A-Z0-9_]+$")
    role_name: str = Field(min_length=1, description="The name of the role")
    auth_required: bool = Field(default=True, description="Whether the role requires authentication")
    is_system_role: bool = Field(default=False, description="Whether the role is a system role")
    status: RoleStatus = Field(default=RoleStatus.ACTIVE, description="The status of the role")
    description: Optional[str] = Field(default=None, description="The description of the role")

    @field_validator("role_code", mode="before")
    @classmethod
    def normalize_role_code(cls, v: str) -> str:
        return trim_and_reject_blank(v).upper()

    @field_validator("role_name", mode="before")
    @classmethod
    def normalize_role_name(cls, v: str) -> str:
        return trim_and_reject_blank(v)

class RoleCreateRequest(RoleBase):
    pass

class RoleCreate(RoleCreateRequest):
    created_by_id: Optional[int] = Field(default=None, description="The ID of the user who created the role")

class RoleUpdateRequest(BaseModel):
    role_name: Optional[str] = Field(min_length=1, max_length=200, default=None, description="The name of the role")
    auth_required: Optional[bool] = Field(default=None, description="Whether the role requires authentication")
    status: Optional[RoleStatus] = Field(default=None, description="The status of the role")
    description: Optional[str] = Field(default=None, description="The description of the role")

    @field_validator("role_name")
    @classmethod
    def normalize_role_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return trim_and_reject_blank(v)

class RoleUpdate(RoleUpdateRequest):
    updated_by_id: Optional[int] = Field(default=None, description="The ID of the user who updated the role")
    deleted_by_id: Optional[int] = Field(default=None, description="The ID of the user who deleted the role")
    deleted_at: Optional[datetime] = Field(default=None, description="The date and time the role was deleted")

class RoleResponse(RoleBase):
    id: int
    created_at: datetime = Field(description="The date and time the role was created")
    created_by_id: Optional[int] = Field(default=None, description="The ID of the user who created the role")
    updated_at: Optional[datetime] = Field(default=None, description="The date and time the role was updated")
    updated_by_id: Optional[int] = Field(default=None, description="The ID of the user who updated the role")
    deleted_at: Optional[datetime] = Field(default=None, description="The date and time the role was deleted")
    deleted_by_id: Optional[int] = Field(default=None, description="The ID of the user who deleted the role")
    model_config = ConfigDict(from_attributes=True) # this allows us to access attributes by dot notation like role.id instead of role["id"]

# Role Permissions Schemas
class RolePermissionBase(BaseModel):
    permission_id: int = Field(description="The ID of the permission")
    priority: int = Field(default=100, ge=0, description="The priority of the role permission")

class AssignRolePermission(RolePermissionBase):
    status: RolePermissionStatus = Field(default=RolePermissionStatus.ACTIVE, description="The status of the role permission")
    effect: RolePermissionEffect = Field(default=RolePermissionEffect.ALLOW, description="The effect of the role permission")
    valid_from: Optional[datetime] = Field(default=None, description="The date and time the role permission becomes valid")
    valid_until: Optional[datetime] = Field(default=None, description="The date and time the role permission becomes invalid")
    notes: Optional[str] = Field(default=None, description="The notes of the role permission")

    @model_validator(mode="after")
    def validate_assign_payload(self):
        if self.status == RolePermissionStatus.DELETED:
            raise ValueError("Cannot assign a role permission with status DELETED")

        if self.valid_from and self.valid_until and self.valid_from >= self.valid_until:
            raise ValueError("valid_from must be earlier than valid_until")
        
        return self

class AssignPermissionsToRoleRequest(BaseModel):
    role_permissions: list[AssignRolePermission] = Field(min_length=1, description="The role permissions to assign to the role")
    
class AssignPermissionsToRole(AssignPermissionsToRoleRequest):
    role_id: int = Field(description="The ID of the role")
    created_by_id: Optional[int] = Field(default=None, description="The ID of the user who assigned the permissions to the role")

class RevokeRolePermission(BaseModel):
    role_permission_id: int = Field(description="The ID of the role permission")
    notes: Optional[str] = Field(default=None, description="The notes of the role permission")

class RevokePermissionsFromRoleRequest(BaseModel):
    role_permissions: list[RevokeRolePermission] = Field(min_length=1, description="The role permissions to revoke from the role")

class RevokePermissionsFromRole(RevokePermissionsFromRoleRequest):
    role_id: int = Field(description="The ID of the role")
    updated_by_id: int = Field(description="The ID of the user who updated the assignment of permissions to the role")
    deleted_by_id: int = Field(description="The ID of the user who deleted the assignment of permissions to the role")
    deleted_at: datetime = Field(default_factory=utcnow, description="The date and time the assignment of permissions to the role was deleted")

class RolePermissionUpdateRequest(BaseModel):
    status: Optional[RolePermissionStatus] = Field(default=None, description="The status of the role permission")
    effect: Optional[RolePermissionEffect] = Field(default=None, description="The effect of the role permission")
    priority: Optional[int] = Field(default=None, ge=0, description="The priority of the role permission")
    valid_from: Optional[datetime] = Field(default=None, description="The date and time the role permission becomes valid")
    valid_until: Optional[datetime] = Field(default=None, description="The date and time the role permission becomes invalid")
    notes: Optional[str] = Field(default=None, description="The notes of the role permission")

    @model_validator(mode="after")
    def validate_validity_window(self):
        if self.valid_from and self.valid_until and self.valid_from >= self.valid_until:
            raise ValueError("valid_from must be earlier than valid_until")
        
        return self

class RolePermissionUpdate(RolePermissionUpdateRequest):
    updated_by_id: Optional[int] = Field(default=None, description="The ID of the user who updated the role permission")
    deleted_by_id: Optional[int] = Field(default=None, description="The ID of the user who deleted the role permission")
    deleted_at: Optional[datetime] = Field(default=None, description="The date and time the role permission was deleted")

class RolePermissionResponse(RolePermissionBase):
    id: int
    role_id: int = Field(description="The ID of the role")
    role_code: Optional[str] = Field(default=None, description="The code of the role")
    role_status: Optional[RoleStatus] = Field(default=None, description="The status of the role")
    permission_code: Optional[str] = Field(default=None, description="The code of the permission")
    permission_status: Optional[PermissionStatus] = Field(default=None, description="The status of the permission")
    status: RolePermissionStatus = Field(description="The status of the role permission")
    effect: RolePermissionEffect = Field(description="The effect of the role permission")
    valid_from: Optional[datetime] = Field(default=None, description="The date and time the role permission becomes valid")
    valid_until: Optional[datetime] = Field(default=None, description="The date and time the role permission becomes invalid")
    notes: Optional[str] = Field(default=None, description="The notes of the role permission")
    created_at: datetime = Field(description="The date and time the role permission was created")
    created_by_id: Optional[int] = Field(default=None, description="The ID of the user who created the role permission")
    updated_at: Optional[datetime] = Field(default=None, description="The date and time the role permission was updated")
    updated_by_id: Optional[int] = Field(default=None, description="The ID of the user who updated the role permission")
    deleted_at: Optional[datetime] = Field(default=None, description="The date and time the role permission was deleted")
    deleted_by_id: Optional[int] = Field(default=None, description="The ID of the user who deleted the role permission")
    model_config = ConfigDict(from_attributes=True)

class AssignPermissionsToRoleOutcome(BaseModel):
    permission_id: int
    priority: int
    role_permission: Optional[RolePermissionResponse]
    status: str
    message: Optional[str]

class AssignPermissionsToRoleResponse(PartialSuccessResponse):
    role_id: int
    outcomes: list[AssignPermissionsToRoleOutcome]

class RevokePermissionsFromRoleOutcome(BaseModel):
    role_permission_id: int
    role_permission: Optional[RolePermissionResponse]
    status: str
    message: Optional[str]

class RevokePermissionsFromRoleResponse(PartialSuccessResponse):
    role_id: int
    outcomes: list[RevokePermissionsFromRoleOutcome]


# User Roles Schemas
class UserRoleBase(BaseModel):
    role_id: int = Field(description="The ID of the role")
    status: UserRoleStatus = Field(default=UserRoleStatus.ACTIVE, description="The status of the user role")
    valid_from: Optional[datetime] = Field(default=None, description="The date and time the user role becomes valid")
    valid_until: Optional[datetime] = Field(default=None, description="The date and time the user role becomes invalid")
    reason: Optional[str] = Field(default=None, description="The reason for the user role")

    @model_validator(mode="after")
    def validate_window(self):
        if self.valid_from and self.valid_until and self.valid_from >= self.valid_until:
            raise ValueError("valid_from must be earlier than valid_until")
        return self

class AssignUserRole(UserRoleBase):

    @model_validator(mode="after")
    def validate_assign_status(self):
        if self.status == UserRoleStatus.DELETED or self.status == UserRoleStatus.REVOKED:
            raise ValueError(f"Cannot assign user role with status {self.status.value}")
        return self

class AssignRolesToUserRequest(BaseModel):
    user_roles: list[AssignUserRole] = Field(min_length=1, description="The user roles to assign to the user")

class AssignRolesToUser(AssignRolesToUserRequest):
    user_id: int = Field(description="The ID of the user")
    created_by_id: Optional[int] = Field(default=None, description="The ID of the user who created the user role")
    assigned_by_id: Optional[int] = Field(default=None, description="The ID of the user who assigned the user role")
    assigned_at: datetime = Field(default_factory=utcnow, description="The date and time the user role was assigned")

class RevokeUserRole(BaseModel):
    user_role_id: int = Field(description="The ID of the user role")
    reason: Optional[str] = Field(default=None, description="The reason for the user role")

class RevokeRolesFromUserRequest(BaseModel):
    user_roles: list[RevokeUserRole] = Field(min_length=1, description="The user roles to revoke from the user")

class RevokeRolesFromUser(RevokeRolesFromUserRequest):
    user_id: int = Field(description="The ID of the user")
    updated_by_id: Optional[int] = Field(description="The ID of the user who updated the user role")
    revoked_by_id: Optional[int] = Field(description="The ID of the user who revoked the user role")
    revoked_at: datetime = Field(default_factory=utcnow, description="The date and time the user role was revoked")

class UserRoleUpdateRequest(BaseModel):
    status: Optional[UserRoleStatus] = Field(default=None, description="The status of the user role")
    valid_from: Optional[datetime] = Field(default=None, description="The date and time the user role becomes valid")
    valid_until: Optional[datetime] = Field(default=None, description="The date and time the user role becomes invalid")
    reason: Optional[str] = Field(default=None, description="The reason for the user role")

    @model_validator(mode="after")
    def validate_status_and_valid_window(self):
        if self.status == UserRoleStatus.DELETED or self.status == UserRoleStatus.REVOKED:
            raise ValueError(f"Use {self.status.value.lower()[:-1]} user role endpoint to {self.status.value.lower()[:-1]} a user role")

        if self.valid_from and self.valid_until and self.valid_from >= self.valid_until:
            raise ValueError("valid_from must be earlier than valid_until")

        return self

class UserRoleUpdate(UserRoleUpdateRequest):
    updated_by_id: int = Field(description="The ID of the user who updated the user role")

class UserRoleDelete(BaseModel):
    updated_by_id: int = Field(description="The ID of the user who updated the user role")
    status: UserRoleStatus = Field(default=UserRoleStatus.DELETED, description="The status of the user role")
    deleted_by_id: Optional[int] = Field(default=None, description="The ID of the user who deleted the user role")
    deleted_at: Optional[datetime] = Field(default=None, description="The date and time the user role was deleted")

    @model_validator(mode="after")
    def validate_delete_metadata(self):
        if self.deleted_by_id is None or self.deleted_at is None:
            raise ValueError("deleted_by_id and deleted_at are required when deleting a user role")
        return self

class UserRoleResponse(UserRoleBase):
    id: int
    user_id: int = Field(description="The ID of the user")
    user_code: Optional[str] = Field(default=None, description="The code of the user")
    user_status: Optional[UserStatus] = Field(default=None, description="The status of the user")
    role_code: Optional[str] = Field(default=None, description="The code of the role")
    role_status: Optional[RoleStatus] = Field(default=None, description="The status of the role")
    created_at: datetime = Field(description="The date and time the user role was created")
    created_by_id: Optional[int] = Field(default=None, description="The ID of the user who created the user role")
    updated_at: Optional[datetime] = Field(default=None, description="The date and time the user role was updated")
    updated_by_id: Optional[int] = Field(default=None, description="The ID of the user who updated the user role")
    assigned_at: Optional[datetime] = Field(default=None, description="The date and time the user role was assigned")
    assigned_by_id: Optional[int] = Field(default=None, description="The ID of the user who assigned the user role")
    revoked_at: Optional[datetime] = Field(default=None, description="The date and time the user role was revoked")
    revoked_by_id: Optional[int] = Field(default=None, description="The ID of the user who revoked the user role")
    deleted_at: Optional[datetime] = Field(default=None, description="The date and time the user role was deleted")
    deleted_by_id: Optional[int] = Field(default=None, description="The ID of the user who deleted the user role")
    model_config = ConfigDict(from_attributes=True)

class AssignRolesToUserOutcome(BaseModel):
    role_id: int
    user_role: Optional[UserRoleResponse]
    status: str
    message: Optional[str]

class AssignRolesToUserResponse(PartialSuccessResponse):
    user_id: int
    outcomes: list[AssignRolesToUserOutcome]

class RevokeRolesFromUserOutcome(BaseModel):
    user_role_id: int
    user_role: Optional[UserRoleResponse]
    status: str
    message: Optional[str]

class RevokeRolesFromUserResponse(PartialSuccessResponse):
    user_id: int
    outcomes: list[RevokeRolesFromUserOutcome]