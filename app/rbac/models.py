from __future__ import annotations
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, BigInteger, Text, Enum as SAEnum, text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from app.db.mixins import AuditMixin
from app.user.models import User

from ..db.models import Base
from ..core.utils import utcnow

class PermissionCategory(str, Enum):
    VIEW = "view"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    EXPORT = "export"
    ASSIGN = "assign"
    REVOKE = "revoke"
    EXECUTE = "execute"
    OVERRIDE = "override"

class PermissionStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    DELETED = "Deleted"
    DEPRECATED = "Deprecated"

class Permission(AuditMixin, Base):
    __tablename__ = "permissions"
    __table_args__ = (
        Index(
            "uq_permissions_permission_code_not_deleted",
            "permission_code",
            unique=True,
            postgresql_where=text("status <> 'Deleted'")
        ),
        CheckConstraint(
            f"permission_code ~ '^[A-Z0-9_]{{3,80}}$'",
            name="ck_permissions_permission_code_format",
        ),
        CheckConstraint(
            "length(btrim(permission_code)) > 0 AND length(btrim(permission_name)) > 0 AND length(btrim(module)) > 0",
            name="ck_permissions_important_fields_not_blank",
        ),
        CheckConstraint(
            "((status = 'Deleted' AND deleted_at IS NOT NULL AND deleted_by_id IS NOT NULL) "
            "OR (status <> 'Deleted' AND deleted_at IS NULL AND deleted_by_id IS NULL))",
            name="ck_permissions_deleted_fields_consistency"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    permission_code: Mapped[str] = mapped_column(Text, nullable=False)
    permission_name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    module: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[PermissionCategory] = mapped_column(
        SAEnum(PermissionCategory, 
        values_callable=lambda x: [e.value for e in x]), 
        nullable=False,
        default=PermissionCategory.VIEW
    )
    is_system_permission: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[PermissionStatus] = mapped_column(
        SAEnum(PermissionStatus, 
        values_callable=lambda x: [e.value for e in x]), 
        nullable=False,
        default=PermissionStatus.ACTIVE
    )

    role_links: Mapped[list["RolePermission"]] = relationship("RolePermission", back_populates="permission")
    
    def __repr__(self) -> str:
        return f"Permission(id={self.id}, permission_code={self.permission_code}, permission_name={self.permission_name})"

class RoleStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    DELETED = "Deleted"
    SUSPENDED = "Suspended"

class Role(AuditMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (
        Index(
            "uq_roles_role_code_not_deleted",
            "role_code",
            unique=True,
            postgresql_where=text("status <> 'Deleted'")
        ),
        CheckConstraint(
            "((status = 'Deleted' AND deleted_at IS NOT NULL AND deleted_by_id IS NOT NULL) "
            "OR (status <> 'Deleted' AND deleted_at IS NULL AND deleted_by_id IS NULL))",
            name="ck_roles_deleted_fields_consistency"
        ),
        CheckConstraint(
            "length(btrim(role_code)) > 0 AND length(btrim(role_name)) > 0",
            name="ck_roles_important_fields_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_code: Mapped[str] = mapped_column(Text, nullable=False)
    role_name: Mapped[str] = mapped_column(Text, nullable=False)
    auth_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[RoleStatus] = mapped_column(
        SAEnum(RoleStatus, values_callable=lambda x: [e.value for e in x]), 
        nullable=False,
        default=RoleStatus.ACTIVE
    )
    is_system_role: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    permission_links: Mapped[list["RolePermission"]] = relationship("RolePermission", back_populates="role")
    user_links: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="role")

    def __repr__(self) -> str:
        return f"Role(id={self.id}, role_code={self.role_code}, role_name={self.role_name})"

class RolePermissionStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    DELETED = "Deleted"
    SUSPENDED = "Suspended"

class RolePermissionEffect(str, Enum):
    ALLOW = "Allow"
    DENY = "Deny"

class RolePermission(AuditMixin, Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        CheckConstraint(
            "((status = 'Deleted' AND deleted_at IS NOT NULL AND deleted_by_id IS NOT NULL) "
            "OR (status <> 'Deleted' AND deleted_at IS NULL AND deleted_by_id IS NULL))",
            name="ck_role_permissions_deleted_fields_consistency"
        ),
        CheckConstraint(
            "valid_from IS NULL OR valid_until IS NULL OR valid_from < valid_until",
            name="ck_role_permissions_valid_dates_consistency"
        ),
        CheckConstraint(
            "priority >= 0",
            name="ck_role_permissions_priority_not_negative"
        ),
        Index(
            "uq_role_permissions_effective",
            "role_id", "permission_id", "priority",
            unique=True,
            # effective-time is intentionally constrained to timeless assignments only.
            # Avoid CURRENT_TIMESTAMP/now() in index predicates (non-immutable/time-dependent).
            postgresql_where=text(
                "status = 'Active' "
            )
        )
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    role: Mapped["Role"] = relationship("Role", foreign_keys=[role_id], overlaps="permission_links")

    permission_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("permissions.id", ondelete="RESTRICT"), nullable=False)
    permission: Mapped["Permission"] = relationship("Permission", foreign_keys=[permission_id], overlaps="role_links")

    status: Mapped[RolePermissionStatus] = mapped_column(
        SAEnum(RolePermissionStatus, values_callable=lambda x: [e.value for e in x]), 
        nullable=False,
        default=RolePermissionStatus.ACTIVE
    )
    effect: Mapped[RolePermissionEffect] = mapped_column(
        SAEnum(RolePermissionEffect, values_callable=lambda x: [e.value for e in x]), 
        nullable=False,
        default=RolePermissionEffect.ALLOW)
    priority: Mapped[int] = mapped_column(nullable=False, default=100)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"RolePermission(id={self.id}, role_id={self.role_id}, permission_id={self.permission_id}, priority={self.priority})"


class UserRoleStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    DELETED = "Deleted"
    SUSPENDED = "Suspended"
    REVOKED = "Revoked"

class UserRole(AuditMixin, Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        CheckConstraint(
            "((status = 'Deleted' AND deleted_at IS NOT NULL AND deleted_by_id IS NOT NULL) "
            "OR (status <> 'Deleted' AND deleted_at IS NULL AND deleted_by_id IS NULL))",
            name="ck_user_roles_deleted_fields_consistency"
        ),
        CheckConstraint(
            "((status = 'Revoked' AND revoked_at IS NOT NULL AND revoked_by_id IS NOT NULL) "
            "OR (status <> 'Revoked' AND revoked_at IS NULL AND revoked_by_id IS NULL))",
            name="ck_user_roles_revoked_fields_consistency"
        ),
        CheckConstraint(
            "valid_from IS NULL OR valid_until IS NULL OR valid_from < valid_until",
            name="ck_user_roles_valid_window"
        ),
        Index(
            "uq_user_roles_effective", "user_id", "role_id",
            unique=True,
            # effective-time is intentionally constrained to timeless assignments only.
            # Avoid CURRENT_TIMESTAMP/now() in index predicates (non-immutable/time-dependent).
            postgresql_where=text(
                "status = 'Active' "
            )
        )
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    user: Mapped["User"] = relationship(
        foreign_keys=[user_id], 
        back_populates="roles_assigned",
        overlaps="created_by, updated_by, revoked_by, assigned_by"
    )

    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    role: Mapped["Role"] = relationship(foreign_keys=[role_id], back_populates="user_links")

    status: Mapped[UserRoleStatus] = mapped_column(
        SAEnum(UserRoleStatus, values_callable=lambda x: [e.value for e in x]), 
        nullable=False,
        default=UserRoleStatus.ACTIVE
    )
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by_id: Mapped[int | None] = mapped_column(
        BigInteger, 
        ForeignKey("users.id", ondelete="RESTRICT"), 
        nullable=True,
    )
    assigned_by_id: Mapped[int | None] = mapped_column(
        BigInteger, 
        ForeignKey("users.id", ondelete="RESTRICT"), 
        nullable=True,
    )

    revoked_by: Mapped["User"] = relationship(
        foreign_keys=[revoked_by_id],
        overlaps="roles_assigned, created_by, updated_by, assigned_by, deleted_by"
    )
    assigned_by: Mapped["User"] = relationship(
        foreign_keys=[assigned_by_id],
        overlaps="roles_assigned, created_by, updated_by, revoked_by, deleted_by"
    )
    
    def __repr__(self) -> str:
        return f"UserRole(id={self.id}, user_id={self.user_id}, role_id={self.role_id})"