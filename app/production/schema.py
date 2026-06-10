from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.core.config import settings
from app.production.models import MachineStatus, RecipeStatus, RecipeVersionStatus, SKUStatus, RepositoryImageStatus
from datetime import datetime
from typing import Optional, Literal
from app.core.utils import trim_and_reject_blank


# Machines
class MachineBase(BaseModel):
    machine_code: str = Field(pattern=r"^MFUK_M[0-9]{2}$")
    machine_name: str
    status: MachineStatus = Field(default=MachineStatus.ACTIVE)
    reason: Optional[str] = Field(default=None)

    @field_validator("machine_code", mode="before")
    @classmethod
    def normalize_machine_code(cls, v: str) -> str:
        return trim_and_reject_blank(v).upper()

    @field_validator("machine_name", mode="before")
    @classmethod
    def normalize_machine_name(cls, v: str) -> str:
        return trim_and_reject_blank(v)

class MachineCreateRequest(MachineBase):
    pass

class MachineCreate(MachineCreateRequest):
    created_by_id: Optional[int] = Field(default=None)

class MachineUpdateRequest(BaseModel):
    machine_name: Optional[str] = Field(default=None)
    status: Optional[MachineStatus] = Field(default=None)
    reason: Optional[str] = Field(default=None)

    @field_validator("machine_name", mode="before")
    @classmethod
    def normalize_machine_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return trim_and_reject_blank(v)

class MachineUpdate(MachineUpdateRequest):
    updated_by_id: Optional[int] = Field(default=None)
    deleted_by_id: Optional[int] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)

class MachineRecipe(BaseModel):
    recipe_id: int
    recipe_code: str
    recipe_name: str
    sku_id: int

class MachineResponse(MachineBase):
    id: int
    machine_recipes: list[MachineRecipe] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)
    created_by_id: Optional[int] = Field(default=None)
    updated_by_id: Optional[int] = Field(default=None)
    deleted_by_id: Optional[int] = Field(default=None)
    model_config = ConfigDict(from_attributes=True)

# SKUs
class SKUBase(BaseModel):
    sku_code: str = Field(pattern=r"^[A-Z0-9_]{3,80}$")
    sku_name: str
    status: SKUStatus = Field(default=SKUStatus.DRAFT)
    description: Optional[str] = Field(default=None)

    @field_validator("sku_code", mode="before")
    @classmethod
    def normalize_sku_code(cls, v: str) -> str:
        return trim_and_reject_blank(v).upper()

    @field_validator("sku_name", mode="before")
    @classmethod
    def normalize_sku_name(cls, v: str) -> str:
        return trim_and_reject_blank(v)

class SKUCreateRequest(SKUBase):
    pass

class SKUCreate(SKUCreateRequest):
    created_by_id: Optional[int] = Field(default=None)

class SKUUpdateRequest(BaseModel):
    sku_name: Optional[str] = Field(default=None)
    status: Optional[SKUStatus] = Field(default=None)
    description: Optional[str] = Field(default=None)

    @field_validator("sku_name", mode="before")
    @classmethod
    def normalize_sku_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return trim_and_reject_blank(v)

class SKUUpdate(SKUUpdateRequest):
    updated_by_id: Optional[int] = Field(default=None)
    deleted_by_id: Optional[int] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)

class SKURecipe(BaseModel):
    recipe_id: int
    recipe_code: str
    recipe_name: str
    machine_id: int

class SKUResponse(SKUBase):
    id: int
    sku_recipes: list[SKURecipe] = Field(default_factory=list)
    thumbnail_url: Optional[str] = Field(default=None)
    created_at: datetime
    updated_at: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)
    created_by_id: Optional[int] = Field(default=None)
    updated_by_id: Optional[int] = Field(default=None)
    deleted_by_id: Optional[int] = Field(default=None)
    model_config = ConfigDict(from_attributes=True)

# Recipes
class RecipeBase(BaseModel):
    sku_id: int
    machine_id: int
    recipe_code: str = Field(pattern=r"^[A-Z0-9._-]{3,80}$")
    recipe_name: str
    status: RecipeStatus = Field(default=RecipeStatus.ACTIVE)
    description: Optional[str] = Field(default=None)

    @field_validator("recipe_code", mode="before")
    @classmethod
    def normalize_recipe_code(cls, v: str) -> str:
        return trim_and_reject_blank(v).upper()
    
    @field_validator("recipe_name", mode="before")
    @classmethod
    def normalize_recipe_name(cls, v: str) -> str:
        return trim_and_reject_blank(v)
    
class RecipeCreateRequest(RecipeBase):
    pass

class RecipeCreate(RecipeCreateRequest):
    created_by_id: Optional[int] = Field(default=None)

class RecipeUpdateRequest(BaseModel):
    recipe_name: Optional[str] = Field(default=None)
    status: Optional[RecipeStatus] = Field(default=None)
    description: Optional[str] = Field(default=None)
    
    @field_validator("recipe_name", mode="before")
    @classmethod
    def normalize_recipe_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return trim_and_reject_blank(v)

class RecipeUpdate(RecipeUpdateRequest):
    updated_by_id: Optional[int] = Field(default=None)
    deleted_by_id: Optional[int] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)

class RecipeResponse(RecipeBase):
    id: int
    sku_code: Optional[str] = Field(default=None)
    machine_code: Optional[str] = Field(default=None)
    reference_image_url: Optional[str] = Field(default=None)
    created_at: datetime
    updated_at: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)
    created_by_id: Optional[int] = Field(default=None)
    updated_by_id: Optional[int] = Field(default=None)
    deleted_by_id: Optional[int] = Field(default=None)
    current_released_version: Optional[str] = Field(default=None)
    model_config = ConfigDict(from_attributes=True)

# Recipe Versions
class RecipeVersionBase(BaseModel):
    version_code: str = Field(pattern=r"^[A-Z0-9._-]{3,80}$")
    version_name: str
    change_summary: Optional[str] = Field(default=None)
    engineering_reason: Optional[str] = Field(default=None)
    source_version_id: Optional[int] = Field(default=None)
    approval_required: bool = Field(default=True)

    @field_validator("version_code", mode="before")
    @classmethod
    def normalize_version_code(cls, v: str) -> str:
        return trim_and_reject_blank(v).upper()

    @field_validator("version_name", mode="before")
    @classmethod
    def normalize_version_name(cls, v: str) -> str:
        return trim_and_reject_blank(v)

class RecipeVersionCreateRequest(RecipeVersionBase):
    pass

class RecipeVersionCreate(RecipeVersionCreateRequest):
    recipe_id: int
    version_no: int = Field(default=1)
    created_by_id: Optional[int] = Field(default=None)


class RecipeVersionUpdateRequest(BaseModel):
    version_name: Optional[str] = Field(default=None)
    status: Optional[RecipeVersionStatus] = Field(default=None)
    change_summary: Optional[str] = Field(default=None)
    engineering_reason: Optional[str] = Field(default=None)
    approval_required: Optional[bool] = Field(default=None)

    @field_validator("version_name", mode="before")
    @classmethod
    def normalize_version_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return trim_and_reject_blank(v)

class RecipeVersionUpdate(RecipeVersionUpdateRequest):
    version_no: Optional[int] = Field(default=None)
    superseded_by_version_id: Optional[int] = Field(default=None)
    superseded_at: Optional[datetime] = Field(default=None)
    approved_at: Optional[datetime] = Field(default=None)
    released_at: Optional[datetime] = Field(default=None)
    archived_at: Optional[datetime] = Field(default=None)
    updated_by_id: Optional[int] = Field(default=None)
    deleted_by_id: Optional[int] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)

class RecipeVersionResponse(RecipeVersionBase):
    id: int
    recipe_id: int
    recipe_code: Optional[str] = Field(default=None)
    status: RecipeVersionStatus
    version_no: int
    superseded_by_version_id: Optional[int] = Field(default=None)
    created_at: datetime
    updated_at: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)
    superseded_at: Optional[datetime] = Field(default=None)
    approved_at: Optional[datetime] = Field(default=None)
    released_at: Optional[datetime] = Field(default=None)
    archived_at: Optional[datetime] = Field(default=None)
    created_by_id: Optional[int] = Field(default=None)
    updated_by_id: Optional[int] = Field(default=None)
    deleted_by_id: Optional[int] = Field(default=None)
    approved_by_id: Optional[int] = Field(default=None)
    released_by_id: Optional[int] = Field(default=None)
    archived_by_id: Optional[int] = Field(default=None)
    model_config = ConfigDict(from_attributes=True)


class RepositoryImageInit(BaseModel):
    original_filename: str
    content_type: str

    @field_validator("original_filename", mode="before")
    @classmethod
    def normalize_original_filename(cls, v: str) -> str:
        return trim_and_reject_blank(v)

class RepositoryImageInitRequest(BaseModel):
    images: list[RepositoryImageInit] = Field(min_length=1, max_length=settings.MAX_REPOSITORY_IMAGES_PER_RECIPE_VERSION)

    @field_validator("images", mode="before")
    @classmethod
    def validate_images(cls, v: list[RepositoryImageInit]) -> list[RepositoryImageInit]:
        if len(v) > settings.MAX_REPOSITORY_IMAGES_PER_RECIPE_VERSION:
            raise ValueError(f"Maximum repository images per recipe version is {settings.MAX_REPOSITORY_IMAGES_PER_RECIPE_VERSION}. You are trying to add {len(v)} repository images")
        return v

class RepositoryImageInitResult(BaseModel):
    id: int
    bucket: str
    object_key: str
    upload_url: str
    content_type: str
    original_filename: Optional[str] = Field(default=None)
    status: RepositoryImageStatus = Field(default=RepositoryImageStatus.PENDING)

class RepositoryImageInitResponse(BaseModel):
    recipe_version_id: int
    images: list[RepositoryImageInitResult] = Field(default_factory=list)
    upload_expires_in_seconds: int

class RepositoryImageComplete(BaseModel):
    repository_image_id: int
    width: Optional[int] = Field(default=None)
    height: Optional[int] = Field(default=None)

class RepositoryImageCompleteRequest(BaseModel):
    images: list[RepositoryImageComplete] = Field(min_length=1, max_length=settings.MAX_REPOSITORY_IMAGES_PER_RECIPE_VERSION)

class RepositoryImageCompleteResult(BaseModel):
    id: int
    status: RepositoryImageStatus
    byte_size: Optional[int] = Field(default=None)
    content_type: Optional[str] = Field(default=None)
    download_url: Optional[str] = Field(default=None)

class RepositoryImageCompleteResponse(BaseModel):
    recipe_version_id: int
    images: list[RepositoryImageCompleteResult] = Field(default_factory=list)

class RepositoryImageUpdate(BaseModel):
    original_filename: Optional[str] = Field(default=None)
    status: Optional[RepositoryImageStatus] = Field(default=None)
    byte_size: Optional[int] = Field(default=None)
    width: Optional[int] = Field(default=None)
    height: Optional[int] = Field(default=None)
    content_type: Optional[str] = Field(default=None)
    is_reference: Optional[bool] = Field(default=None)
    updated_by_id: Optional[int] = Field(default=None)
    deleted_by_id: Optional[int] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)

class RepositoryImageResponse(BaseModel):
    id: int
    recipe_version_id: int
    sku_id: Optional[int] = Field(default=None)
    bucket: str
    object_key: str
    original_filename: Optional[str] = Field(default=None)
    content_type: Optional[str] = Field(default=None)
    byte_size: Optional[int] = Field(default=None)
    width: Optional[int] = Field(default=None)
    height: Optional[int] = Field(default=None)
    is_reference: bool = Field(default=False)
    status: RepositoryImageStatus
    created_at: datetime
    updated_at: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)
    created_by_id: Optional[int] = Field(default=None)
    updated_by_id: Optional[int] = Field(default=None)
    deleted_by_id: Optional[int] = Field(default=None)
    download_url: Optional[str] = Field(default=None)
    model_config = ConfigDict(from_attributes=True)

class SetRepositoryImageReferenceResponse(BaseModel):
    recipe_version_id: int
    repository_image_id: int
    message: Literal["Reference updated"]