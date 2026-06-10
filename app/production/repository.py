from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, update
from sqlalchemy.orm import selectinload
from app.core.utils import set_attributes
from app.production.models import *
from typing import Sequence
from app.db.session import include_deleted_execution_options
from app.production.schema import *

class ProductionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Machines
    def _machine_load_options(self):
        return (
            selectinload(Machine.recipes),
        )

    async def get_machines(self, include_deleted: bool = False, statuses: Sequence[MachineStatus] | None = None) -> list[Machine]:
        query = select(Machine).options(*self._machine_load_options())
        if statuses:
            query = query.where(Machine.status.in_(statuses))
        result = await self.db.execute(query, execution_options=include_deleted_execution_options(include_deleted))
        return list(result.scalars().all())

    async def get_machine_by_id(self, machine_id: int) -> Machine | None:
        query = select(Machine).where(Machine.id == machine_id).options(*self._machine_load_options())
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_machine_by_code(self, machine_code: str) -> Machine | None:
        query = select(Machine).where(Machine.machine_code == machine_code).options(*self._machine_load_options())
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_machine(self, machine: MachineCreate) -> Machine:
        new_machine = Machine(**machine.model_dump(exclude_unset=True))
        self.db.add(new_machine)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

        await self.db.refresh(new_machine, ["recipes"])
        return new_machine

    async def update_machine(self, machine: Machine, machine_updates: MachineUpdate) -> Machine:
        updated_machine = machine_updates.model_dump(exclude_unset=True)
        set_attributes(machine, updated_machine)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise
        await self.db.refresh(machine, ["recipes"])
        return machine

    # SKUs
    def _sku_load_options(self):
        return (
            selectinload(SKU.recipes),
        )

    async def get_skus(self, include_deleted: bool = False, statuses: Sequence[SKUStatus] | None = None) -> list[SKU]:
        query = select(SKU).options(*self._sku_load_options())
        if statuses:
            query = query.where(SKU.status.in_(statuses))
        result = await self.db.execute(query, execution_options=include_deleted_execution_options(include_deleted))
        return list(result.scalars().all())

    async def get_sku_by_id(self, sku_id: int) -> SKU | None:
        query = select(SKU).where(SKU.id == sku_id).options(*self._sku_load_options())
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def get_sku_by_code(self, sku_code: str) -> SKU | None:
        query = select(SKU).where(SKU.sku_code == sku_code).options(*self._sku_load_options())
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_sku(self, sku: SKUCreate) -> SKU:
        new_sku = SKU(**sku.model_dump(exclude_unset=True))
        self.db.add(new_sku)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

        await self.db.refresh(new_sku, ["recipes"])
        return new_sku

    async def update_sku(self, sku: SKU, sku_updates: SKUUpdate) -> SKU:
        updated_sku = sku_updates.model_dump(exclude_unset=True)
        set_attributes(sku, updated_sku)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise
        await self.db.refresh(sku, ["recipes"])
        return sku

    # Recipes
    def _recipe_load_options(self):
        return (
            selectinload(Recipe.sku),
            selectinload(Recipe.machine),
            selectinload(Recipe.recipe_versions),
        )

    async def get_recipes(
        self, 
        include_deleted: bool = False, 
        statuses: Sequence[RecipeStatus] | None = None,
        sku_id: int | None = None,
        machine_id: int | None = None,
    ) -> list[Recipe]:
        query = select(Recipe).options(*self._recipe_load_options())
        if statuses:
            query = query.where(Recipe.status.in_(statuses))
        if sku_id:
            query = query.where(Recipe.sku_id == sku_id)
        if machine_id:
            query = query.where(Recipe.machine_id == machine_id)
        result = await self.db.execute(query, execution_options=include_deleted_execution_options(include_deleted))
        return list(result.scalars().all())

    async def get_recipe_by_id(self, recipe_id: int) -> Recipe | None:
        query = (
            select(Recipe)
            .where(Recipe.id == recipe_id)
            .options(*self._recipe_load_options())
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_recipe_by_code(self, recipe_code: str) -> Recipe | None:
        query = (
            select(Recipe)
            .where(Recipe.recipe_code == recipe_code)
            .options(*self._recipe_load_options())
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_recipe(self, recipe: RecipeCreate) -> Recipe:
        new_recipe = Recipe(**recipe.model_dump(exclude_unset=True))
        self.db.add(new_recipe)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

        await self.db.refresh(new_recipe, ["recipe_versions"])
        return new_recipe

    async def update_recipe(self, recipe: Recipe, recipe_updates: RecipeUpdate) -> Recipe:
        updated_recipe = recipe_updates.model_dump(exclude_unset=True)
        set_attributes(recipe, updated_recipe)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise
        
        await self.db.refresh(recipe, ["recipe_versions"])
        return recipe

    # Recipe Versions
    def _recipe_version_load_options(self):
        return (
            selectinload(RecipeVersion.recipe),
        )

    async def get_recipe_versions(
        self, 
        recipe_id: int, 
        include_deleted: bool = False, 
        statuses: Sequence[RecipeVersionStatus] | None = None,
    ) -> list[RecipeVersion]:
        query = (
            select(RecipeVersion)
            .where(RecipeVersion.recipe_id == recipe_id)
            .options(*self._recipe_version_load_options())
            .order_by(RecipeVersion.version_no.desc())
        )
        if statuses:
            query = query.where(RecipeVersion.status.in_(statuses))
        result = await self.db.execute(query, execution_options=include_deleted_execution_options(include_deleted))
        return list(result.scalars().all())

    async def get_recipe_version_by_id(self, recipe_version_id: int) -> RecipeVersion | None:
        query = (
            select(RecipeVersion)
            .where(RecipeVersion.id == recipe_version_id)
            .options(*self._recipe_version_load_options())
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_recipe_version_by_code(self, recipe_version_code: str) -> RecipeVersion | None:
        query = (
            select(RecipeVersion)
            .where(RecipeVersion.version_code == recipe_version_code)
            .options(*self._recipe_version_load_options())
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_recipe_version(self, recipe_version: RecipeVersionCreate) -> RecipeVersion:
        new_recipe_version = RecipeVersion(**recipe_version.model_dump(exclude_unset=True, exclude={"recipe_code"}))
        self.db.add(new_recipe_version)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

        await self.db.refresh(new_recipe_version, ["recipe"])
        return new_recipe_version

    async def update_recipe_version(self, recipe_version: RecipeVersion, recipe_version_updates: RecipeVersionUpdate) -> RecipeVersion:
        updated_recipe_version = recipe_version_updates.model_dump(exclude_unset=True)
        set_attributes(recipe_version, updated_recipe_version)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise
        await self.db.refresh(recipe_version, ["recipe"])
        return recipe_version
        
    # Repository Images
    def _repository_image_load_options(self):
        return (
            selectinload(RepositoryImage.recipe_version),
            selectinload(RepositoryImage.sku),
        )

    async def get_repository_images(
        self, 
        recipe_version_id: int | None = None, 
        include_deleted: bool = False, 
        statuses: Sequence[RepositoryImageStatus] | None = None,
        sku_id: int | None = None,
    ) -> list[RepositoryImage]:
        query = select(RepositoryImage).options(*self._repository_image_load_options())
        if recipe_version_id:
            query = query.where(RepositoryImage.recipe_version_id == recipe_version_id)
        if statuses:
            query = query.where(RepositoryImage.status.in_(statuses))
        if sku_id:
            query = query.where(RepositoryImage.sku_id == sku_id)
        result = await self.db.execute(query, execution_options=include_deleted_execution_options(include_deleted))
        return list(result.scalars().all())

    async def get_repository_image_by_id(self, repository_image_id: int) -> RepositoryImage | None:
        query = (
            select(RepositoryImage)
            .where(RepositoryImage.id == repository_image_id)
            .options(*self._repository_image_load_options())
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_repository_images_by_ids(
        self, 
        ids: list[int],
        recipe_version_id: int | None = None,
        include_deleted: bool = False,
    ) -> list[RepositoryImage]:
        if not ids:
            return []
        query = (
            select(RepositoryImage)
            .where(RepositoryImage.id.in_(ids))
            .options(*self._repository_image_load_options())
        )
        if recipe_version_id:
            query = query.where(RepositoryImage.recipe_version_id == recipe_version_id)

        result = await self.db.execute(query, execution_options=include_deleted_execution_options(include_deleted))
        return list(result.scalars().all())

    async def create_repository_images(self, repository_images: list[RepositoryImage]) -> list[RepositoryImage]:
        self.db.add_all(repository_images)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

        for repository_image in repository_images:
            await self.db.refresh(repository_image, ["recipe_version", "sku"])

        return repository_images

    async def count_repository_images(self, recipe_version_id: int, include_deleted: bool = False) -> int:
        query = select(func.count(RepositoryImage.id)).where(RepositoryImage.recipe_version_id == recipe_version_id)
        result = await self.db.execute(query, execution_options=include_deleted_execution_options(include_deleted))
        return result.scalar() or 0

    async def update_repository_image(self, repository_image: RepositoryImage, repository_image_updates: RepositoryImageUpdate) -> RepositoryImage:
        updated_repository_image = repository_image_updates.model_dump(exclude_unset=True)
        set_attributes(repository_image, updated_repository_image)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise
        await self.db.refresh(repository_image, ["recipe_version", "sku"])
        return repository_image

    async def clear_reference_flags(self, recipe_version_id: int) -> None:
        stmt = (
            update(RepositoryImage)
            .where(RepositoryImage.recipe_version_id == recipe_version_id)
            .where(RepositoryImage.is_reference.is_(True))
            .values(is_reference=False)
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def get_sku_thumbnail(self, sku_id: int) -> RepositoryImage | None:
        """SKU thumbnail is the reference image of the RELEASED recipe version"""
        query = (
            select(RepositoryImage)
            .join(RecipeVersion, RecipeVersion.id == RepositoryImage.recipe_version_id)
            .join(Recipe, Recipe.id == RecipeVersion.recipe_id)
            .where(RepositoryImage.sku_id == sku_id)
            .where(RecipeVersion.status == RecipeVersionStatus.RELEASED)
            .where(RepositoryImage.is_reference.is_(True))
            .where(RepositoryImage.status == RepositoryImageStatus.ACTIVE)
            .order_by(Recipe.machine_id.asc())
            .limit(1)
            .options(*self._repository_image_load_options())
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_recipe_reference_image(self, recipe_id: int) -> RepositoryImage | None:
        query = (
            select(RepositoryImage)
            .join(RecipeVersion, RecipeVersion.id == RepositoryImage.recipe_version_id)
            .join(Recipe, Recipe.id == RecipeVersion.recipe_id)
            .where(Recipe.id == recipe_id)
            .where(RecipeVersion.status == RecipeVersionStatus.RELEASED)
            .where(RepositoryImage.is_reference.is_(True))
            .where(RepositoryImage.status == RepositoryImageStatus.ACTIVE)
            .options(*self._repository_image_load_options())
        )
        result = await self.db.execute(query)
        return result.scalars().first()