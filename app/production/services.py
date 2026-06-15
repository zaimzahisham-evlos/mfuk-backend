import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.pagination import PaginatedResponse, PaginationParams, to_paginated_response
from app.core.utils import utcnow
from app.production.helpers import allow_recipe_version_status_transitions, is_recipe_version_immutable, to_machine_response, to_recipe_response, to_recipe_version_response, to_sku_response
from app.production.models import *
from app.production.schema import *
from app.production.repository import ProductionRepository
from app.storage.dependencies import get_storage_client
from app.storage.helpers import build_repository_image_key
from app.core.config import settings


class ProductionService:
    def __init__(self, db: AsyncSession):
        self.repo = ProductionRepository(db)

    # Machines
    async def get_machines(
        self, 
        include_deleted: bool = False, 
        statuses: Sequence[MachineStatus] | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResponse[MachineResponse]:
        total = await self.repo.count_machines(include_deleted, statuses, pagination.search if pagination else None)
        machines = await self.repo.get_machines(include_deleted, statuses, pagination)
        items = [to_machine_response(machine) for machine in machines]
        return to_paginated_response(items, total, pagination)

    async def get_machine_by_id(self, machine_id: int) -> MachineResponse:
        machine = await self.repo.get_machine_by_id(machine_id)
        if not machine:
            raise NotFoundError(f"Machine with ID {machine_id} not found")
        return to_machine_response(machine)

    async def get_machine_by_code(self, machine_code: str) -> MachineResponse:
        machine_code = machine_code.strip().upper()
        machine = await self.repo.get_machine_by_code(machine_code)
        if not machine:
            raise NotFoundError(f"Machine with code {machine_code} not found")
        return to_machine_response(machine)

    async def create_machine(self, machine: MachineCreate) -> MachineResponse:
        if machine.status == MachineStatus.DELETED:
            raise BadRequestError("Cannot create a machine with status Deleted")
        
        existing_machine = await self.repo.get_machine_by_code(machine.machine_code.strip().upper())
        if existing_machine:
            raise BadRequestError(f"Machine with code {machine.machine_code} already exists")

        try:
            new_machine = await self.repo.create_machine(machine)
        except IntegrityError as e:
            logging.error(f"Error creating machine: {e}")
            raise BadRequestError(f"Invalid machine payload or conflicting machine data")
        return to_machine_response(new_machine)

    async def update_machine(self, machine_code: str, machine_updates: MachineUpdate) -> MachineResponse:
        machine_code = machine_code.strip().upper()
        existing_machine = await self.repo.get_machine_by_code(machine_code)
        if not existing_machine:
            raise NotFoundError(f"Machine with code {machine_code} not found")

        if machine_updates.status == MachineStatus.DELETED:
            raise BadRequestError("Cannot update a machine to deleted. Use delete machine endpoint instead.")

        if machine_updates.status and not machine_updates.reason:
            raise BadRequestError(f"Cannot update a machine status to {machine_updates.status.value.lower()} without a reason")

        try:
            updated_machine = await self.repo.update_machine(existing_machine, machine_updates)
        except IntegrityError as e:
            logging.error(f"Error updating machine: {e}")
            raise BadRequestError(f"Invalid machine payload or conflicting machine data")
        
        return to_machine_response(updated_machine)

    async def delete_machine(self, machine_code: str, deleted_by_id: int) -> None:
        machine_code = machine_code.strip().upper()
        existing_machine = await self.repo.get_machine_by_code(machine_code)
        if not existing_machine:
            raise NotFoundError(f"Machine with code {machine_code} not found")

        recipes = await self.repo.get_recipes(machine_id=existing_machine.id)
        if recipes:
            raise BadRequestError("Cannot delete a machine with recipes")

        machine_updates = MachineUpdate(
            status=MachineStatus.DELETED,
            deleted_by_id=deleted_by_id,
            deleted_at=utcnow(),
            updated_by_id=deleted_by_id,
        )

        try:
            await self.repo.update_machine(existing_machine, machine_updates)
        except IntegrityError as e:
            logging.error(f"Error deleting machine: {e}")
            raise BadRequestError(f"Invalid machine payload or conflicting machine data")

    # SKUs
    async def _to_sku_response(self, sku: SKU) -> SKUResponse:
        dto = to_sku_response(sku)
        thumbnail = await self.repo.get_sku_thumbnail(sku.id)
        if thumbnail:
            dto.thumbnail_url = get_storage_client().presign_get(thumbnail.bucket, thumbnail.object_key)
        return dto
    
    async def get_skus(
        self, 
        include_deleted: bool = False, 
        statuses: Sequence[SKUStatus] | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResponse[SKUResponse]:
        total = await self.repo.count_skus(include_deleted, statuses, pagination.search if pagination else None)
        skus = await self.repo.get_skus(include_deleted, statuses, pagination)
        items = [await self._to_sku_response(sku) for sku in skus]
        return to_paginated_response(items, total, pagination)


    async def get_sku_by_id(self, sku_id: int) -> SKUResponse:
        sku = await self.repo.get_sku_by_id(sku_id)
        if not sku:
            raise NotFoundError(f"SKU with ID {sku_id} not found")
        return await self._to_sku_response(sku)

    async def get_sku_by_code(self, sku_code: str) -> SKUResponse:
        sku_code = sku_code.strip().upper()
        sku = await self.repo.get_sku_by_code(sku_code)
        if not sku:
            raise NotFoundError(f"SKU with code {sku_code} not found")
        return await self._to_sku_response(sku)

    async def create_sku(self, sku: SKUCreate) -> SKUResponse:
        if sku.status == SKUStatus.DELETED:
            raise BadRequestError("Cannot create an SKU with status Deleted")

        existing_sku = await self.repo.get_sku_by_code(sku.sku_code.strip().upper())
        if existing_sku:
            raise BadRequestError(f"SKU with code {sku.sku_code} already exists")

        try:
            new_sku = await self.repo.create_sku(sku)
        except IntegrityError as e:
            logging.error(f"Error creating SKU: {e}")
            raise BadRequestError(f"Invalid SKU payload or conflicting SKU data")
        return await self._to_sku_response(new_sku)

    async def update_sku(self, sku_code: str, sku_updates: SKUUpdate) -> SKUResponse:
        sku_code = sku_code.strip().upper()
        existing_sku = await self.repo.get_sku_by_code(sku_code)
        if not existing_sku:
            raise NotFoundError(f"SKU with code {sku_code} not found")

        if sku_updates.status == SKUStatus.DELETED:
            sku_updates = sku_updates.model_copy(update={
                "deleted_by_id": sku_updates.updated_by_id,
                "deleted_at": utcnow(),
            })

        try:
            updated_sku = await self.repo.update_sku(existing_sku, sku_updates)
        except IntegrityError as e:
            logging.error(f"Error updating SKU: {e}")
            raise BadRequestError(f"Invalid SKU payload or conflicting SKU data")
        return await self._to_sku_response(updated_sku)

    async def delete_sku(self, sku_code: str, deleted_by_id: int) -> None:
        sku_code = sku_code.strip().upper()
        existing_sku = await self.repo.get_sku_by_code(sku_code)
        if not existing_sku:
            raise NotFoundError(f"SKU with code {sku_code} not found")

        recipes = await self.repo.get_recipes(sku_id=existing_sku.id)
        if recipes:
            raise BadRequestError("Cannot delete an SKU with recipes")

        sku_updates = SKUUpdate(
            status=SKUStatus.DELETED,
            deleted_by_id=deleted_by_id,
            deleted_at=utcnow(),
            updated_by_id=deleted_by_id,
        )

        try:
            await self.repo.update_sku(existing_sku, sku_updates)
        except IntegrityError as e:
            logging.error(f"Error deleting SKU: {e}")
            raise BadRequestError(f"Invalid SKU payload or conflicting SKU data")

    # Recipes
    async def _to_recipe_response(self, recipe: Recipe) -> RecipeResponse:
        dto = to_recipe_response(recipe)
        reference_image = await self.repo.get_recipe_reference_image(recipe.id)
        if reference_image:
            dto.reference_image_url = get_storage_client().presign_get(reference_image.bucket, reference_image.object_key)
        return dto

    async def get_recipes(
        self, 
        include_deleted: bool = False, 
        statuses: Sequence[RecipeStatus] | None = None,
        sku_id: int | None = None,
        machine_id: int | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResponse[RecipeResponse]:
        total = await self.repo.count_recipes(include_deleted, statuses, sku_id, machine_id, pagination.search if pagination else None)
        recipes = await self.repo.get_recipes(include_deleted, statuses, sku_id, machine_id, pagination)
        items = [await self._to_recipe_response(recipe) for recipe in recipes]
        return to_paginated_response(items, total, pagination)

    async def get_recipe_by_id(self, recipe_id: int) -> RecipeResponse:
        recipe = await self.repo.get_recipe_by_id(recipe_id)
        if not recipe:
            raise NotFoundError(f"Recipe with ID {recipe_id} not found")
        return await self._to_recipe_response(recipe)
    
    async def get_recipe_by_code(self, recipe_code: str) -> RecipeResponse:
        recipe_code = recipe_code.strip().upper()
        recipe = await self.repo.get_recipe_by_code(recipe_code)
        if not recipe:
            raise NotFoundError(f"Recipe with code {recipe_code} not found")
        return await self._to_recipe_response(recipe)
    
    async def create_recipe(self, recipe: RecipeCreate) -> RecipeResponse:
        """
        assign recipe to an SKU and a machine, enforce one recipe per SKU and machine
        """
        if recipe.status == RecipeStatus.DELETED:
            raise BadRequestError("Cannot create a recipe with status Deleted")

        existing_recipe = await self.repo.get_recipe_by_code(recipe.recipe_code.strip().upper())
        if existing_recipe:
            raise BadRequestError(f"Recipe with code {recipe.recipe_code} already exists")

        existing_sku = await self.repo.get_sku_by_id(recipe.sku_id)
        if not existing_sku:
            raise NotFoundError(f"SKU with ID {recipe.sku_id} not found")

        existing_machine = await self.repo.get_machine_by_id(recipe.machine_id)
        if not existing_machine:
            raise NotFoundError(f"Machine with ID {recipe.machine_id} not found")

        # enforce one recipe per SKU and machine
        existing_recipes = await self.repo.get_recipes(sku_id=recipe.sku_id, machine_id=recipe.machine_id)
        if existing_recipes:
            raise BadRequestError(f"Recipe with SKU {recipe.sku_id} and machine {recipe.machine_id} already exists")

        try:
            new_recipe = await self.repo.create_recipe(recipe)
        except IntegrityError as e:
            logging.error(f"Error creating recipe: {e}")
            orig = getattr(e, "orig", None)
            diag = getattr(orig, "diag", None) if orig else None
            name = getattr(diag, "constraint_name", None) if diag else None

            if name == "uq_recipes_sku_machine_not_deleted":
                raise BadRequestError(
                    f"A recipe already exists for SKU {recipe.sku_id} and machine {recipe.machine_id}"
                )
            if name == "uq_recipes_recipe_code_not_deleted":
                raise BadRequestError(f"Recipe with code {recipe.recipe_code} already exists")

            logging.exception(f"Unexpected integrity error creating recipe: {e}")
            raise BadRequestError(f"Invalid recipe payload or conflicting recipe data")
        return await self._to_recipe_response(new_recipe)
    
    async def update_recipe(self, recipe_code: str, recipe_updates: RecipeUpdate) -> RecipeResponse:
        recipe_code = recipe_code.strip().upper()
        existing_recipe = await self.repo.get_recipe_by_code(recipe_code)
        if not existing_recipe:
            raise NotFoundError(f"Recipe with code {recipe_code} not found")

        if recipe_updates.status == RecipeStatus.DELETED:
            recipe_versions = await self.repo.get_recipe_versions(recipe_id=existing_recipe.id, statuses=[RecipeVersionStatus.RELEASED])
            if recipe_versions:
                raise BadRequestError("Cannot delete a recipe with released recipe versions")

            recipe_updates = recipe_updates.model_copy(update={
                "deleted_by_id": recipe_updates.updated_by_id,
                "deleted_at": utcnow(),
            })

        try:
            updated_recipe = await self.repo.update_recipe(existing_recipe, recipe_updates)
        except IntegrityError as e:
            logging.error(f"Error updating recipe: {e}")
            raise BadRequestError(f"Invalid recipe payload or conflicting recipe data")
        return await self._to_recipe_response(updated_recipe)

    async def delete_recipe(self, recipe_code: str, deleted_by_id: int) -> None:
        recipe_code = recipe_code.strip().upper()
        existing_recipe = await self.repo.get_recipe_by_code(recipe_code)
        if not existing_recipe:
            raise NotFoundError(f"Recipe with code {recipe_code} not found")

        recipe_versions = await self.repo.get_recipe_versions(recipe_id=existing_recipe.id, statuses=[RecipeVersionStatus.RELEASED])
        if recipe_versions:
            raise BadRequestError("Cannot delete a recipe with released recipe versions")

        recipe_updates = RecipeUpdate(
            status=RecipeStatus.DELETED,
            deleted_by_id=deleted_by_id,
            deleted_at=utcnow(),
            updated_by_id=deleted_by_id,
        )

        try:
            await self.repo.update_recipe(existing_recipe, recipe_updates)
        except IntegrityError as e:
            logging.error(f"Error deleting recipe: {e}")
            raise BadRequestError(f"Invalid recipe payload or conflicting recipe data")

    # Recipe Versions
    async def get_recipe_versions(
        self, recipe_code: str, 
        include_deleted: bool = False, 
        statuses: Sequence[RecipeVersionStatus] | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResponse[RecipeVersionResponse]:
        recipe = await self.get_recipe_by_code(recipe_code)
        total = await self.repo.count_recipe_versions(recipe.id, include_deleted, statuses, pagination.search if pagination else None)
        recipe_versions = await self.repo.get_recipe_versions(recipe.id, include_deleted, statuses, pagination)
        items = [to_recipe_version_response(recipe_version) for recipe_version in recipe_versions]
        return to_paginated_response(items, total, pagination)

    async def get_recipe_version_by_id(self, recipe_version_id: int) -> RecipeVersionResponse:
        recipe_version = await self.repo.get_recipe_version_by_id(recipe_version_id)
        if not recipe_version:
            raise NotFoundError(f"Recipe version with ID {recipe_version_id} not found")
        return to_recipe_version_response(recipe_version)
    
    async def get_recipe_version_by_code(self, recipe_version_code: str) -> RecipeVersionResponse:
        recipe_version_code = recipe_version_code.strip().upper()
        recipe_version = await self.repo.get_recipe_version_by_code(recipe_version_code)
        if not recipe_version:
            raise NotFoundError(f"Recipe version with code {recipe_version_code} not found")
        return to_recipe_version_response(recipe_version)

    async def create_recipe_version(self, recipe_version: RecipeVersionCreate) -> RecipeVersionResponse:
        existing_recipe_version = await self.repo.get_recipe_version_by_code(recipe_version.version_code)
        if existing_recipe_version:
            raise BadRequestError(f"Recipe version with code {recipe_version.version_code} already exists")

        existing_recipe_versions = await self.repo.get_recipe_versions(recipe_version.recipe_id, include_deleted=True)
        if existing_recipe_versions:
            recipe_version.version_no = existing_recipe_versions[0].version_no + 1 #[0] is the latest (order by desc)

        if recipe_version.source_version_id: # copy from source recipe version
            source_recipe_version = await self.get_recipe_version_by_id(recipe_version.source_version_id)
            if source_recipe_version.recipe_id != recipe_version.recipe_id:
                raise BadRequestError(f"Source recipe version {recipe_version.source_version_id} does not belong to recipe {recipe_version.recipe_id}")
            
            recipe_version = recipe_version.model_copy(update={
                "engineering_reason": recipe_version.engineering_reason or f"Copy of {source_recipe_version.version_name}",
                "source_version_id": source_recipe_version.id,
            })
            # TODO: copies the recipe_steps under recipe version to the new recipe version

        try:
            new_recipe_version = await self.repo.create_recipe_version(recipe_version)
        except IntegrityError as e:
            logging.error(f"Error creating recipe version: {e}")
            raise BadRequestError(f"Invalid recipe version payload or conflicting recipe version data")
        except Exception as e:
            logging.error(f"Error creating recipe version: {e}")
            raise BadRequestError(f"Unexpected error creating recipe version")

        return to_recipe_version_response(new_recipe_version)
    
    async def update_recipe_version(self, recipe_version_code: str, recipe_version_updates: RecipeVersionUpdate) -> RecipeVersionResponse:
        recipe_version = await self.repo.get_recipe_version_by_code(recipe_version_code)
        if not recipe_version:
            raise NotFoundError(f"Recipe version with code {recipe_version_code} not found")

        if is_recipe_version_immutable(recipe_version.status):
            raise BadRequestError(f"Cannot update a {recipe_version.status.value.lower()} recipe version")

        if (
            recipe_version.status == RecipeVersionStatus.ARCHIVED
            and recipe_version_updates.status is not None
            and recipe_version_updates.status != RecipeVersionStatus.DRAFT
        ):
            raise BadRequestError("Archived recipe versions can only transition to Draft")

        if recipe_version_updates.status and \
            not allow_recipe_version_status_transitions(recipe_version.status, recipe_version_updates.status, recipe_version.approval_required):
            raise BadRequestError(f"Cannot update recipe version from {recipe_version.status.value.lower()} to {recipe_version_updates.status.value.lower()}")
        
        if recipe_version_updates.status == RecipeVersionStatus.ARCHIVED:
            recipe_version_updates = recipe_version_updates.model_copy(update={
                "archived_at": utcnow(),
                "archived_by_id": recipe_version_updates.updated_by_id,
            })

        if recipe_version_updates.status == RecipeVersionStatus.APPROVED:
            recipe_version_updates = recipe_version_updates.model_copy(update={
                "approved_at": utcnow(),
                "approved_by_id": recipe_version_updates.updated_by_id,
            })

        try:
            # if released version exists, update it to superseded and this new version to released
            if recipe_version_updates.status == RecipeVersionStatus.RELEASED:
                released_recipe_versions = await self.repo.get_recipe_versions(recipe_version.recipe_id, statuses=[RecipeVersionStatus.RELEASED])
                if released_recipe_versions:
                    released_version = released_recipe_versions[0]
                    released_version_updates = RecipeVersionUpdate(
                        status=RecipeVersionStatus.SUPERSEDED,
                        superseded_at=utcnow(),
                        superseded_by_version_id=recipe_version.id,
                        updated_by_id=recipe_version_updates.updated_by_id,
                    )
                    await self.repo.update_recipe_version(released_version, released_version_updates)

                recipe_version_updates = recipe_version_updates.model_copy(update={
                    "released_at": utcnow(),
                    "released_by_id": recipe_version_updates.updated_by_id,
                    "superseded_by_version_id": None,
                    "superseded_at": None,
                })
            updated_recipe_version = await self.repo.update_recipe_version(recipe_version, recipe_version_updates)
        except IntegrityError as e:
            logging.error(f"Error updating recipe version: {e}")
            raise BadRequestError(f"Invalid recipe version payload or conflicting recipe version data")
        except Exception as e:
            logging.error(f"Error updating recipe version: {e}")
            raise BadRequestError(f"Unexpected error updating recipe version")

        return to_recipe_version_response(updated_recipe_version)

    async def delete_recipe_version(self, recipe_version_code: str, deleted_by_id: int) -> None:
        recipe_version = await self.repo.get_recipe_version_by_code(recipe_version_code)
        if not recipe_version:
            raise NotFoundError(f"Recipe version with code {recipe_version_code} not found")

        if recipe_version.status == RecipeVersionStatus.RELEASED:
            raise BadRequestError("Cannot delete a released recipe version")

        recipe_version_updates = RecipeVersionUpdate(
            status=RecipeVersionStatus.DELETED,
            deleted_by_id=deleted_by_id,
            deleted_at=utcnow(),
            updated_by_id=deleted_by_id,
        )

        try:
            await self.repo.update_recipe_version(recipe_version, recipe_version_updates)
        except IntegrityError as e:
            logging.error(f"Error deleting recipe version: {e}")
            raise BadRequestError(f"Invalid recipe version payload or conflicting recipe version data")
        except Exception as e:
            logging.error(f"Error deleting recipe version: {e}")
            raise BadRequestError(f"Unexpected error deleting recipe version")

    # Repository Images
    async def init_repository_images(
       self, 
       recipe_version_code: str,
       payload: RepositoryImageInitRequest,
       created_by_id: int,
    ) -> RepositoryImageInitResponse:
        recipe_version = await self.repo.get_recipe_version_by_code(recipe_version_code.strip().upper())
        if not recipe_version:
            raise NotFoundError(f"Recipe version with code {recipe_version_code} not found")

        if is_recipe_version_immutable(recipe_version.status):
            raise BadRequestError(f"Cannot init repository images for a {recipe_version.status.value.lower()} recipe version")

        existing_count = await self.repo.count_repository_images_by_recipe_version_id(recipe_version.id)
        
        if existing_count + len(payload.images) > settings.MAX_REPOSITORY_IMAGES_PER_RECIPE_VERSION:
            raise BadRequestError((
                f"Maximum repository images per recipe version is {settings.MAX_REPOSITORY_IMAGES_PER_RECIPE_VERSION}. "
                f"You can only add up to {settings.MAX_REPOSITORY_IMAGES_PER_RECIPE_VERSION - existing_count} more repository images"
            ))

        storage_client = get_storage_client()
        repository_images: list[RepositoryImage] = []

        for image in payload.images:
            if image.content_type not in settings.ALLOWED_IMAGE_CONTENT_TYPES:
                raise BadRequestError(
                    (
                        f"Content type {image.content_type} is not allowed. "
                        f"Allowed content types are {', '.join(settings.ALLOWED_IMAGE_CONTENT_TYPES)}"
                    )
                )
            key = build_repository_image_key(recipe_version.version_code, image.original_filename)
            repository_images.append(
                RepositoryImage(
                    recipe_version_id=recipe_version.id,
                    sku_id=recipe_version.recipe.sku_id,
                    bucket=settings.S3_BUCKET_REPOSITORY_IMAGES,
                    object_key=key,
                    original_filename=image.original_filename,
                    content_type=image.content_type,
                    status=RepositoryImageStatus.PENDING,
                    created_by_id=created_by_id,
                )
            )

        try:
            created_repository_images = await self.repo.create_repository_images(repository_images)
            images: list[RepositoryImageInitResult] = []
            for repository_image in created_repository_images:
                upload_url = storage_client.presign_put(
                    repository_image.bucket, 
                    repository_image.object_key,
                    repository_image.content_type or "application/octet-stream",
                )
                images.append(
                    RepositoryImageInitResult(
                        id=repository_image.id,
                        bucket=repository_image.bucket,
                        object_key=repository_image.object_key,
                        upload_url=upload_url,
                        content_type=repository_image.content_type or "application/octet-stream",
                        original_filename=repository_image.original_filename,
                        status=repository_image.status,
                    )
                )
            return RepositoryImageInitResponse(
                recipe_version_id=recipe_version.id,
                images=images,
                upload_expires_in_seconds=settings.S3_PRESIGN_UPLOAD_EXPIRE_SECONDS,
            )
        except IntegrityError as e:
            logging.error(f"Error creating repository images: {e}")
            raise BadRequestError(f"Invalid repository images payload or conflicting repository images data")
        except Exception as e:
            logging.error(f"Error creating repository images: {e}")
            raise BadRequestError(f"Unexpected error creating repository images")


    async def complete_repository_images(
        self,
        recipe_version_code: str,
        payload: RepositoryImageCompleteRequest,
        updated_by_id: int,
    ) -> RepositoryImageCompleteResponse:
        recipe_version = await self.repo.get_recipe_version_by_code(recipe_version_code.strip().upper())
        if not recipe_version:
            raise NotFoundError(f"Recipe version with code {recipe_version_code} not found")

        if is_recipe_version_immutable(recipe_version.status):
            raise BadRequestError(f"Cannot complete repository images for a {recipe_version.status.value.lower()} recipe version")

        ids = [image.repository_image_id for image in payload.images]
        repository_images = await self.repo.get_repository_images_by_ids(ids, recipe_version.id)
        
        if len(repository_images) != len(ids):
            found_ids = [image.id for image in repository_images]
            missing = [rid for rid in ids if rid not in found_ids]
            raise BadRequestError(f"Repository image IDs not found for recipe version {recipe_version_code}: {missing}")

        storage_client = get_storage_client()
        images: list[RepositoryImageCompleteResult] = []
        payload_by_id = {image.repository_image_id: image for image in payload.images}

        for image in repository_images:
            if image.status == RepositoryImageStatus.ACTIVE:
                # idempotent behavior - return current state
                download_url = storage_client.presign_get(image.bucket, image.object_key)
                images.append(
                    RepositoryImageCompleteResult(
                        id=image.id,
                        status=image.status,
                        byte_size=image.byte_size,
                        content_type=image.content_type,
                        download_url=download_url,
                    )
                )
                continue

            try:
                head = storage_client.head(image.bucket, image.object_key)
            except Exception:
                raise BadRequestError(f"Uploaded object not found for repository image {image.id}")

            byte_size = head.get("ContentLength")
            content_type = head.get("ContentType") or image.content_type

            if not byte_size:
                raise BadRequestError(f"Invalid object byte size metadata for repository image {image.id}")
            
            if byte_size > settings.MAX_REPOSITORY_IMAGE_BYTES:
                max_megabytes = int(settings.MAX_REPOSITORY_IMAGE_BYTES / 1024 / 1024)
                raise BadRequestError(f"Repository image {image.id} is too large. Maximum repository image size is {max_megabytes} MB")

            if content_type and content_type not in settings.ALLOWED_IMAGE_CONTENT_TYPES:
                raise BadRequestError((
                    f"Repository image {image.id} has an unsupported content type: {content_type}. "
                    f"Allowed content types are {', '.join(settings.ALLOWED_IMAGE_CONTENT_TYPES)}"
                ))
            
            image_payload = payload_by_id[image.id]
            image_updates = RepositoryImageUpdate(
                status=RepositoryImageStatus.ACTIVE,
                byte_size=byte_size,
                content_type=content_type,
                width=image_payload.width,
                height=image_payload.height,
                updated_by_id=updated_by_id,
            )
            try:
                updated_image = await self.repo.update_repository_image(image, image_updates)
                download_url = storage_client.presign_get(updated_image.bucket, updated_image.object_key)
                images.append(
                    RepositoryImageCompleteResult(
                        id=updated_image.id,
                        status=updated_image.status,
                        byte_size=updated_image.byte_size,
                        content_type=updated_image.content_type,
                        download_url=download_url,
                    )
                )
            except IntegrityError as e:
                logging.error(f"Error updating repository image: {e}")
                raise BadRequestError(f"Invalid repository image payload or conflicting repository image data")
            except Exception as e:
                logging.error(f"Error updating repository image: {e}")
                raise BadRequestError(f"Unexpected error updating repository image")

        return RepositoryImageCompleteResponse(
            recipe_version_id=recipe_version.id,
            images=images,
        )

    async def get_repository_images(
        self,
        recipe_version_code: str,
        include_deleted: bool = False,
        statuses: Sequence[RepositoryImageStatus] | None = None,
        sku_id: int | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResponse[RepositoryImageResponse]:
        recipe_version = await self.get_recipe_version_by_code(recipe_version_code)

        if sku_id: 
            await self.get_sku_by_id(sku_id)

        storage_client = get_storage_client()
        total = await self.repo.count_repository_images(recipe_version.id, include_deleted, statuses, sku_id, pagination.search if pagination else None)
        images = await self.repo.get_repository_images(recipe_version.id, include_deleted, statuses, sku_id, pagination)
        results: list[RepositoryImageResponse] = []
        for image in images:
            dto = RepositoryImageResponse.model_validate(image)
            if image.status == RepositoryImageStatus.ACTIVE:
                dto.download_url = storage_client.presign_get(image.bucket, image.object_key)
            results.append(dto)
        return to_paginated_response(results, total, pagination)

    async def delete_repository_images(
        self,
        repository_image_ids: list[int],
        deleted_by_id: int,
    ) -> str:
        repository_images = await self.repo.get_repository_images_by_ids(repository_image_ids)

        storage_client = get_storage_client()
        
        skipped_reference_ids = []
        for image in repository_images:
            if is_recipe_version_immutable(image.recipe_version.status):
                raise BadRequestError((
                    f"Cannot delete repository image for id {image.id} " 
                    f"because it belongs to recipe version {image.recipe_version_id} " 
                    f"with status {image.recipe_version.status.value.lower()}"
                ))
            if image.is_reference:
                skipped_reference_ids.append(image.id)
                continue

            storage_client.delete(image.bucket, image.object_key)
            try:
                await self.repo.update_repository_image(image, RepositoryImageUpdate(
                    status=RepositoryImageStatus.DELETED,
                    deleted_by_id=deleted_by_id,
                    deleted_at=utcnow(),
                    updated_by_id=deleted_by_id,
                    is_reference=False,
                )) 
            except IntegrityError as e:
                logging.error(f"Error deleting repository image: {e}")
                raise BadRequestError(f"Invalid repository image payload or conflicting repository image data for id {image.id}")
            except Exception as e:
                logging.error(f"Error deleting repository image: {e}")
                raise BadRequestError(f"Unexpected error deleting repository image for id {image.id}")

        if skipped_reference_ids:
            return f"Deleted {len(repository_image_ids) - len(skipped_reference_ids)} repository images and skipped {len(skipped_reference_ids)} reference repository images with ids {skipped_reference_ids}"
        
        return f"Deleted {len(repository_image_ids)} repository images"

    async def set_reference_from_repository_image(
        self,
        repository_image_id: int,
        updated_by_id: int,
    ) -> SetRepositoryImageReferenceResponse:
        repository_image = await self.repo.get_repository_image_by_id(repository_image_id)
        if not repository_image:
            raise NotFoundError(f"Repository image with id {repository_image_id} not found")

        if repository_image.status != RepositoryImageStatus.ACTIVE:
            raise BadRequestError(f"Repository image with id {repository_image_id} is not active")
        
        try:
            await self.repo.clear_reference_flags(repository_image.recipe_version_id) # clear any existing reference flags. ensure only one reference per recipe version.
            await self.repo.update_repository_image(repository_image, RepositoryImageUpdate(
                is_reference=True,
                updated_by_id=updated_by_id,
            ))
            return SetRepositoryImageReferenceResponse(
                recipe_version_id=repository_image.recipe_version_id,
                repository_image_id=repository_image.id,
                message="Reference updated",
            )
        except IntegrityError as e:
            logging.error(f"Error setting repository image reference: {e}")
            raise BadRequestError(f"Invalid repository image payload or conflicting repository image data")
        except Exception as e:
            logging.error(f"Error setting repository image reference: {e}")
            raise BadRequestError(f"Unexpected error setting repository image reference")
