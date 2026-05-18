from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy import DateTime, BigInteger, ForeignKey

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