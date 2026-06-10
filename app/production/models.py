from __future__ import annotations
from enum import Enum
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, Index, Text, text, Enum as SAEnum, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.mixins import AuditMixin
from app.db.models import Base
from app.user.models import User

class MachineStatus(str, Enum):
    COMMISSIONING = "Commissioning"
    ACTIVE = "Active"
    MAINTENANCE = "Maintenance"
    DECOMMISSIONED = "Decommissioned"
    DELETED = "Deleted"

class Machine(AuditMixin, Base):
    __tablename__ = "machines"
    __table_args__ = (
        Index(
            "uq_machines_machine_code_not_deleted",
            "machine_code",
            unique=True,
            postgresql_where=text("status <> 'Deleted'")
        ),
        CheckConstraint(
            f"machine_code ~ '^MFUK_M[0-9]{{2}}$'",
            name="ck_machines_machine_code_format",
        ),
        CheckConstraint(
            "length(btrim(machine_code)) > 0 AND length(btrim(machine_name)) > 0",
            name="ck_machines_important_fields_not_blank",
        ),
        CheckConstraint(
            "((status = 'Deleted' AND deleted_at IS NOT NULL AND deleted_by_id IS NOT NULL) "
            "OR (status <> 'Deleted' AND deleted_at IS NULL AND deleted_by_id IS NULL))",
            name="ck_machines_deleted_fields_consistency"
        ),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    machine_code: Mapped[str] = mapped_column(Text, nullable=False)
    machine_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[MachineStatus] = mapped_column(
        SAEnum(MachineStatus, values_callable=lambda x: [e.value for e in x]), 
        nullable=False, 
        default=MachineStatus.ACTIVE
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    recipes: Mapped[list["Recipe"]] = relationship("Recipe", back_populates="machine")

    def __repr__(self) -> str:
        return f"Machine(id={self.id}, machine_code={self.machine_code}, machine_name={self.machine_name})"


class SKUStatus(str, Enum):
    DRAFT = "Draft"
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    OBSOLETE = "Obsolete"
    DELETED = "Deleted"


class SKU(AuditMixin, Base):
    __tablename__ = "skus"
    __table_args__ = (
        Index(
            "uq_skus_sku_code_not_deleted",
            "sku_code",
            unique=True,
            postgresql_where=text("status <> 'Deleted'")
        ),
        CheckConstraint(
            f"sku_code ~ '^[A-Z0-9_]{{3,80}}$'",
            name="ck_skus_sku_code_format",
        ),
        CheckConstraint(
            "length(btrim(sku_code)) > 0 AND length(btrim(sku_name)) > 0",
            name="ck_skus_important_fields_not_blank",
        ),
        CheckConstraint(
            "((status = 'Deleted' AND deleted_at IS NOT NULL AND deleted_by_id IS NOT NULL) "
            "OR (status <> 'Deleted' AND deleted_at IS NULL AND deleted_by_id IS NULL))",
            name="ck_skus_deleted_fields_consistency"
        ),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sku_code: Mapped[str] = mapped_column(Text, nullable=False)
    sku_name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SKUStatus] = mapped_column(
        SAEnum(SKUStatus, values_callable=lambda x: [e.value for e in x]), 
        nullable=False, 
        default=SKUStatus.DRAFT
    )

    recipes: Mapped[list["Recipe"]] = relationship("Recipe", back_populates="sku")
    repository_images: Mapped[list["RepositoryImage"]] = relationship("RepositoryImage", back_populates="sku")

    def __repr__(self) -> str:
        return f"SKU(id={self.id}, sku_code={self.sku_code}, sku_name={self.sku_name})"


class RecipeStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    OBSOLETE = "Obsolete"
    DELETED = "Deleted"


class Recipe(AuditMixin, Base):
    __tablename__ = "recipes"
    __table_args__ = (
        Index(
            "uq_recipes_recipe_code_not_deleted",
            "recipe_code",
            unique=True,
            postgresql_where=text("status <> 'Deleted'")
        ),
        Index(
            "uq_recipes_sku_machine_not_deleted",
            "sku_id", "machine_id",
            unique=True,
            postgresql_where=text("status <> 'Deleted'")
        ),
        CheckConstraint(
            f"recipe_code ~ '^[A-Z0-9._-]{{3,80}}$'",
            name="ck_recipes_recipe_code_format",
        ),
        CheckConstraint(
            "length(btrim(recipe_code)) > 0 AND length(btrim(recipe_name)) > 0",
            name="ck_recipes_important_fields_not_blank",
        ),
        CheckConstraint(
            "((status = 'Deleted' AND deleted_at IS NOT NULL AND deleted_by_id IS NOT NULL) "
            "OR (status <> 'Deleted' AND deleted_at IS NULL AND deleted_by_id IS NULL))",
            name="ck_recipes_deleted_fields_consistency"
        ),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sku_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("skus.id", ondelete="RESTRICT"), nullable=False)
    sku: Mapped["SKU"] = relationship("SKU", foreign_keys=[sku_id], back_populates="recipes")
    machine_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("machines.id", ondelete="RESTRICT"), nullable=False)
    machine: Mapped["Machine"] = relationship("Machine", foreign_keys=[machine_id], back_populates="recipes")
    recipe_code: Mapped[str] = mapped_column(Text, nullable=False)
    recipe_name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[RecipeStatus] = mapped_column(
        SAEnum(RecipeStatus, values_callable=lambda x: [e.value for e in x]), 
        nullable=False, 
        default=RecipeStatus.ACTIVE
    )
    recipe_versions: Mapped[list["RecipeVersion"]] = relationship("RecipeVersion", back_populates="recipe")

    def __repr__(self) -> str:
        return f"Recipe(id={self.id}, sku_id={self.sku_id}, machine_id={self.machine_id}, recipe_code={self.recipe_code}, recipe_name={self.recipe_name})"


class RecipeVersionStatus(str, Enum):
    DRAFT = "Draft"
    UNDERREVIEW = "UnderReview"
    APPROVED = "Approved"
    RELEASED = "Released"
    SUPERSEDED = "Superseded"
    ARCHIVED = "Archived"
    OBSOLETE = "Obsolete"
    DELETED = "Deleted"

class RecipeVersion(AuditMixin, Base):
    __tablename__ = "recipe_versions"
    __table_args__ = (
        Index(
            "uq_recipe_versions_version_code_not_deleted",
            "version_code",
            unique=True,
            postgresql_where=text("status <> 'Deleted'")
        ),
        Index(
            "uq_recipe_versions_recipe_version_no_not_deleted",
            "recipe_id", "version_no",
            unique=True,
            postgresql_where=text("status <> 'Deleted'")
        ),
        Index(
            "uq_recipe_versions_one_released_per_recipe",
            "recipe_id",
            unique=True,
            postgresql_where=text("status = 'Released'"),
        ),
        CheckConstraint(
            f"version_code ~ '^[A-Z0-9._-]{{3,80}}$'",
            name="ck_recipe_versions_version_code_format",
        ),
        CheckConstraint(
            "length(btrim(version_code)) > 0 AND length(btrim(version_name)) > 0",
            name="ck_recipe_versions_important_fields_not_blank",
        ),
        CheckConstraint(
            "((status = 'Deleted' AND deleted_at IS NOT NULL AND deleted_by_id IS NOT NULL) "
            "OR (status <> 'Deleted' AND deleted_at IS NULL AND deleted_by_id IS NULL))",
            name="ck_recipe_versions_deleted_fields_consistency"
        )
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    recipe_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("recipes.id", ondelete="RESTRICT"), nullable=False)
    recipe: Mapped["Recipe"] = relationship("Recipe", foreign_keys=[recipe_id], back_populates="recipe_versions")
    version_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    version_code: Mapped[str] = mapped_column(Text, nullable=False)
    version_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[RecipeVersionStatus] = mapped_column(
        SAEnum(RecipeVersionStatus, values_callable=lambda x: [e.value for e in x]), 
        nullable=False, 
        default=RecipeVersionStatus.DRAFT
    )
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    engineering_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # self-reference
    source_version_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("recipe_versions.id", ondelete="RESTRICT"), nullable=True)
    source_version: Mapped["RecipeVersion"] = relationship(foreign_keys=[source_version_id], remote_side="RecipeVersion.id", overlaps="superseded_by_version")
    superseded_by_version_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("recipe_versions.id", ondelete="RESTRICT"), nullable=True)
    superseded_by_version: Mapped["RecipeVersion"] = relationship(foreign_keys=[superseded_by_version_id], remote_side="RecipeVersion.id", overlaps="source_version")
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    approval_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    approved_by: Mapped["User"] = relationship("User", foreign_keys=[approved_by_id])

    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_by_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    released_by: Mapped["User"] = relationship("User", foreign_keys=[released_by_id])

    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_by_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    archived_by: Mapped["User"] = relationship("User", foreign_keys=[archived_by_id])

    repository_images: Mapped[list["RepositoryImage"]] = relationship("RepositoryImage", back_populates="recipe_version")

    def __repr__(self) -> str:
        return f"RecipeVersion(id={self.id}, recipe_id={self.recipe_id}, version_no={self.version_no}, version_name={self.version_name})"


class RepositoryImageStatus(str, Enum):
    PENDING = "Pending"
    ACTIVE = "Active"
    DELETED = "Deleted"

class RepositoryImage(AuditMixin, Base):
    __tablename__ = "repository_images"
    __table_args__ = (
        Index(
            "uq_repository_images_object_key_not_deleted",
            "bucket", "object_key",
            unique=True,
            postgresql_where=text("status <> 'Deleted'")
        ),
        Index(
            # only one reference image per recipe version
            "uq_repository_images_reference_true_per_recipe_version",
            "recipe_version_id",
            unique=True,
            postgresql_where=text("is_reference = TRUE"),
        ),
        CheckConstraint(
            "((status = 'Deleted' AND deleted_at IS NOT NULL AND deleted_by_id IS NOT NULL) "
            "OR (status <> 'Deleted' AND deleted_at IS NULL AND deleted_by_id IS NULL))",
            name="ck_repository_images_deleted_fields_consistency"
        ),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    recipe_version_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("recipe_versions.id", ondelete="RESTRICT"), nullable=False)
    recipe_version: Mapped["RecipeVersion"] = relationship("RecipeVersion", foreign_keys=[recipe_version_id], back_populates="repository_images")
    bucket: Mapped[str] = mapped_column(Text, nullable=False)
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    byte_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    sku_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("skus.id", ondelete="RESTRICT"), nullable=True)
    sku: Mapped["SKU"] = relationship("SKU", foreign_keys=[sku_id], back_populates="repository_images")
    is_reference: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[RepositoryImageStatus] = mapped_column(
        SAEnum(RepositoryImageStatus, values_callable=lambda x: [e.value for e in x]), 
        nullable=False, 
        default=RepositoryImageStatus.PENDING
    )