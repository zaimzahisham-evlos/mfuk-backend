from datetime import datetime
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from sqlalchemy import DateTime, BigInteger, ForeignKey
from app.core.utils import utcnow

class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deleted_by_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"), 
        nullable=True
    )

class AuditMixin(SoftDeleteMixin):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=utcnow,
    )
    created_by_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    updated_by_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    
    @declared_attr
    def created_by(cls):
        return relationship("User", foreign_keys=[cls.created_by_id], overlaps="updated_by, deleted_by") # type: ignore
    @declared_attr
    def updated_by(cls):
        return relationship("User", foreign_keys=[cls.updated_by_id], overlaps="created_by, deleted_by") # type: ignore
    @declared_attr
    def deleted_by(cls):
        return relationship("User", foreign_keys=[cls.deleted_by_id], overlaps="created_by, updated_by") # type: ignore