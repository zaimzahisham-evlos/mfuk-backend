from __future__ import annotations
from sqlalchemy import CheckConstraint, Index, BigInteger, Text, Enum as SAEnum, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from app.db.mixins import AuditMixin

from ..db.models import Base

class UserType(str, Enum):
    HUMAN = "Human"
    SYSTEM = "System"
    SERVICE = "Service"
    ROBOT = "Robot"
    PLC = "PLC"

class UserStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    SUSPENDED = "Suspended"
    DELETED = "Deleted"

class User(AuditMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        Index(
            "uq_users_user_code_not_deleted",
            "user_code",
            unique=True,
            postgresql_where=text("status <> 'Deleted'")
        ),
        CheckConstraint(
            "((status = 'Deleted' AND deleted_at IS NOT NULL AND deleted_by_id IS NOT NULL) "
            "OR (status <> 'Deleted' AND deleted_at IS NULL AND deleted_by_id IS NULL))",
            name="ck_users_deleted_fields_consistency"
        ),
        CheckConstraint(
            "length(btrim(user_code)) > 0",
            name="ck_users_user_code_not_blank",
        ),
        CheckConstraint(
            "length(btrim(full_name)) > 0",
            name="ck_users_full_name_not_blank",
        ),
        CheckConstraint(
            "(password_hash IS NULL) OR (status <> 'Deleted' AND user_type IN ('Human'))",
            name="ck_users_password_auth_consistency",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_code: Mapped[str] = mapped_column(Text, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    user_type: Mapped[UserType] = mapped_column(
        SAEnum(UserType, values_callable=lambda x: [e.value for e in x]), 
        nullable=False, 
        default=UserType.HUMAN
    )
    status : Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus, values_callable=lambda x: [e.value for e in x]), 
        nullable=False, 
        default=UserStatus.ACTIVE
    )

    created_by: Mapped["User"] = relationship(foreign_keys="User.created_by_id", remote_side="User.id") # type: ignore
    updated_by: Mapped["User"] = relationship(foreign_keys="User.updated_by_id", remote_side="User.id") # type: ignore
    deleted_by: Mapped["User"] = relationship(foreign_keys="User.deleted_by_id", remote_side="User.id") # type: ignore
    
    roles_assigned: Mapped[list["UserRole"]] = relationship( # type: ignore
        "UserRole",
        foreign_keys="UserRole.user_id",
        back_populates="user",
        overlaps="created_by, updated_by, revoked_by, assigned_by, deleted_by"
    )


    def __repr__(self) -> str:
        return f"User(id={self.id}, user_code={self.user_code}, full_name={self.full_name})"