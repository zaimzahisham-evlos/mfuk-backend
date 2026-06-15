import logging
from fastapi import APIRouter, Response, status, Depends, Query
from app.auth.dependencies import require_permission
from app.core.exceptions import ForbiddenError
from app.core.pagination import PaginatedResponse, PaginationParams
from app.core.utils import utcnow
from app.rbac.services import RbacService
from app.user.schema import UserResponse
from ..production.schema import *
from ..production.services import ProductionService
from typing import Annotated, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.session import get_db

router = APIRouter()

"""Machines"""
@router.get("/machines", response_model=PaginatedResponse[MachineResponse])
async def get_machines(
    current_user: Annotated[UserResponse, Depends(require_permission("MACHINE_VIEW"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    include_deleted: bool = False,
    statuses: Annotated[Sequence[MachineStatus] | None, Query()] = None,
):
    logging.info("Getting machines")
    return await ProductionService(db).get_machines(include_deleted, statuses, pagination)

@router.get("/machines/{machine_code}", response_model=MachineResponse)
async def get_machine_by_code(
    machine_code: str,
    current_user: Annotated[UserResponse, Depends(require_permission("MACHINE_VIEW"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Getting machine with code {machine_code}")
    return await ProductionService(db).get_machine_by_code(machine_code)

@router.post("/machines", response_model=MachineResponse, status_code=status.HTTP_201_CREATED)
async def create_machine(
    machine: MachineCreateRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("MACHINE_CREATE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Creating machine with code {machine.machine_code}")
    machine_create = MachineCreate(
        **machine.model_dump(exclude_unset=True),
        created_by_id=current_user.id
    )
    return await ProductionService(db).create_machine(machine_create)

@router.patch("/machines/{machine_code}", response_model=MachineResponse)
async def update_machine(
    machine_code: str,
    machine: MachineUpdateRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("MACHINE_UPDATE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Updating machine with code {machine_code}")
    machine_update = MachineUpdate(
        **machine.model_dump(exclude_unset=True),
        updated_by_id=current_user.id
    )
    return await ProductionService(db).update_machine(machine_code, machine_update)

@router.delete("/machines/{machine_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_machine(
    machine_code: str,
    current_user: Annotated[UserResponse, Depends(require_permission("MACHINE_DELETE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Deleting machine with code {machine_code}")
    return await ProductionService(db).delete_machine(machine_code, current_user.id)

"""SKUs"""
@router.get("/skus", response_model=PaginatedResponse[SKUResponse])
async def get_skus(
    current_user: Annotated[UserResponse, Depends(require_permission("SKU_VIEW"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    include_deleted: bool = False,
    statuses: Annotated[Sequence[SKUStatus] | None, Query()] = None,
):
    logging.info("Getting SKUs")
    return await ProductionService(db).get_skus(include_deleted, statuses, pagination)

@router.get("/skus/{sku_code}", response_model=SKUResponse)
async def get_sku_by_code(
    sku_code: str,
    current_user: Annotated[UserResponse, Depends(require_permission("SKU_VIEW"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Getting SKU with code {sku_code}")
    return await ProductionService(db).get_sku_by_code(sku_code)

@router.post("/skus", response_model=SKUResponse, status_code=status.HTTP_201_CREATED)
async def create_sku(
    sku: SKUCreateRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("SKU_CREATE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Creating SKU with code {sku.sku_code}")
    sku_create = SKUCreate(
        **sku.model_dump(exclude_unset=True),
        created_by_id=current_user.id
    )
    return await ProductionService(db).create_sku(sku_create)

@router.patch("/skus/{sku_code}", response_model=SKUResponse)
async def update_sku(
    sku_code: str,
    sku: SKUUpdateRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("SKU_UPDATE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Updating SKU with code {sku_code}")
    sku_update = SKUUpdate(
        **sku.model_dump(exclude_unset=True),
        updated_by_id=current_user.id
    )
    return await ProductionService(db).update_sku(sku_code, sku_update)

@router.delete("/skus/{sku_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sku(
    sku_code: str,
    current_user: Annotated[UserResponse, Depends(require_permission("SKU_DELETE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Deleting SKU with code {sku_code}")
    return await ProductionService(db).delete_sku(sku_code, current_user.id)

"""Recipes"""
@router.get("/recipes", response_model=PaginatedResponse[RecipeResponse])
async def get_recipes(
    current_user: Annotated[UserResponse, Depends(require_permission("RECIPE_VIEW"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    include_deleted: bool = False,
    statuses: Annotated[Sequence[RecipeStatus] | None, Query()] = None,
    sku_id: Annotated[int | None, Query()] = None,
    machine_id: Annotated[int | None, Query()] = None,
):
    logging.info("Getting recipes")
    return await ProductionService(db).get_recipes(include_deleted, statuses, sku_id, machine_id, pagination)

@router.get("/recipes/{recipe_code}", response_model=RecipeResponse)
async def get_recipe_by_code(
    recipe_code: str,
    current_user: Annotated[UserResponse, Depends(require_permission("RECIPE_VIEW"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Getting recipe with code {recipe_code}")
    return await ProductionService(db).get_recipe_by_code(recipe_code)

@router.post("/recipes", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe: RecipeCreateRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("RECIPE_CREATE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Creating recipe with code {recipe.recipe_code}")
    recipe_create = RecipeCreate(
        **recipe.model_dump(exclude_unset=True),
        created_by_id=current_user.id
    )
    return await ProductionService(db).create_recipe(recipe_create)

@router.patch("/recipes/{recipe_code}", response_model=RecipeResponse)
async def update_recipe(
    recipe_code: str,
    recipe: RecipeUpdateRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("RECIPE_UPDATE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Updating recipe with code {recipe_code}")

    recipe_update = RecipeUpdate(
        **recipe.model_dump(exclude_unset=True),
        updated_by_id=current_user.id
    )
    return await ProductionService(db).update_recipe(recipe_code, recipe_update)

@router.delete("/recipes/{recipe_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_code: str,
    current_user: Annotated[UserResponse, Depends(require_permission("RECIPE_DELETE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Deleting recipe with code {recipe_code}")
    return await ProductionService(db).delete_recipe(recipe_code, current_user.id)

"""Recipe Versions"""
@router.get("/recipes/{recipe_code}/versions", response_model=PaginatedResponse[RecipeVersionResponse])
async def get_recipe_versions(
    recipe_code: str,
    current_user: Annotated[UserResponse, Depends(require_permission("RECIPE_VERSION_VIEW"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    include_deleted: bool = False,
    statuses: Annotated[Sequence[RecipeVersionStatus] | None, Query()] = [RecipeVersionStatus.RELEASED],
):
    logging.info(f"Getting recipe versions for recipe with code {recipe_code}")
    return await ProductionService(db).get_recipe_versions(recipe_code, include_deleted, statuses, pagination)

@router.get("/recipe-versions/{recipe_version_code}", response_model=RecipeVersionResponse)
async def get_recipe_version_by_code(
    recipe_version_code: str,
    current_user: Annotated[UserResponse, Depends(require_permission("RECIPE_VERSION_VIEW"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Getting recipe version with code {recipe_version_code}")
    return await ProductionService(db).get_recipe_version_by_code(recipe_version_code)

@router.post("/recipes/{recipe_code}/versions", response_model=RecipeVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe_version(
    recipe_code: str,
    recipe_version: RecipeVersionCreateRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("RECIPE_VERSION_CREATE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Creating recipe version for recipe with code {recipe_code}")
    production_service = ProductionService(db)
    recipe = await production_service.get_recipe_by_code(recipe_code)
    recipe_version_create = RecipeVersionCreate(
        **recipe_version.model_dump(exclude_unset=True),
        recipe_id=recipe.id,
        created_by_id=current_user.id
    )
    return await production_service.create_recipe_version(recipe_version_create)

@router.patch("/recipe-versions/{recipe_version_code}", response_model=RecipeVersionResponse)
async def update_recipe_version(
    recipe_version_code: str,
    recipe_version: RecipeVersionUpdateRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("RECIPE_VERSION_UPDATE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Updating recipe version with code {recipe_version_code}")
    rbac_service = RbacService(db)
    if recipe_version.status == RecipeVersionStatus.APPROVED:
        has_permission = await rbac_service.has_permission(current_user.id, "RECIPE_VERSION_APPROVE")
        if not has_permission:
            raise ForbiddenError(detail="You are not allowed to approve recipe versions")

    if recipe_version.status == RecipeVersionStatus.RELEASED:
        # assign permission because there is no release permission category
        # assign fits because release is basically assigning a recipe version to the sku for the machine
        has_permission = await rbac_service.has_permission(current_user.id, "RECIPE_VERSION_ASSIGN")
        if not has_permission:
            raise ForbiddenError(detail="You are not allowed to release recipe versions")

    recipe_version_update = RecipeVersionUpdate(
        **recipe_version.model_dump(exclude_unset=True),
        updated_by_id=current_user.id
    )
    return await ProductionService(db).update_recipe_version(recipe_version_code, recipe_version_update)

@router.delete("/recipe-versions/{recipe_version_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe_version(
    recipe_version_code: str,
    current_user: Annotated[UserResponse, Depends(require_permission("RECIPE_VERSION_DELETE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Deleting recipe version with code {recipe_version_code}")
    return await ProductionService(db).delete_recipe_version(recipe_version_code, current_user.id)

"""Repository Images"""
@router.get("/recipe-versions/{recipe_version_code}/repository-images", response_model=PaginatedResponse[RepositoryImageResponse])
async def get_repository_images(
    recipe_version_code: str,
    current_user: Annotated[UserResponse, Depends(require_permission("REPOSITORY_IMAGE_VIEW"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    include_deleted: bool = False,
    statuses: Annotated[Sequence[RepositoryImageStatus] | None, Query()] = None,
    sku_id: Annotated[int | None, Query()] = None,
):
    logging.info(f"Getting repository images for recipe version with code {recipe_version_code}")
    return await ProductionService(db).get_repository_images(recipe_version_code, include_deleted, statuses, sku_id, pagination)

@router.post(
    "/recipe-versions/{recipe_version_code}/repository-images/init", 
    response_model=RepositoryImageInitResponse,
    status_code=status.HTTP_201_CREATED
)
async def init_repository_images(
    recipe_version_code: str,
    payload: RepositoryImageInitRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("REPOSITORY_IMAGE_CREATE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Initializing repository images for recipe version with code {recipe_version_code}")
    return await ProductionService(db).init_repository_images(recipe_version_code, payload, current_user.id)

@router.patch(
    "/recipe-versions/{recipe_version_code}/repository-images/complete",
    response_model=RepositoryImageCompleteResponse,
)
async def complete_repository_images(
    recipe_version_code: str,
    payload: RepositoryImageCompleteRequest,
    current_user: Annotated[UserResponse, Depends(require_permission("REPOSITORY_IMAGE_UPDATE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Completing repository images for recipe version with code {recipe_version_code}")
    return await ProductionService(db).complete_repository_images(recipe_version_code, payload, current_user.id)

@router.delete("/repository-images")
async def delete_repository_images(
    repository_image_ids: Annotated[list[int], Query()],
    current_user: Annotated[UserResponse, Depends(require_permission("REPOSITORY_IMAGE_DELETE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Deleting repository images with ids {repository_image_ids}")
    message = await ProductionService(db).delete_repository_images(repository_image_ids, current_user.id)
    return Response(content=message, status_code=status.HTTP_200_OK)

@router.patch("/repository-images/{repository_image_id}/set-reference", response_model=SetRepositoryImageReferenceResponse)
async def set_reference_from_repository_image(
    repository_image_id: int,
    current_user: Annotated[UserResponse, Depends(require_permission("REPOSITORY_IMAGE_UPDATE"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logging.info(f"Setting reference for repository image with id {repository_image_id}")
    return await ProductionService(db).set_reference_from_repository_image(repository_image_id, current_user.id)

