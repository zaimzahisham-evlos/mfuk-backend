

from app.core.exceptions import BadRequestError
from app.production.models import Recipe, RecipeVersionStatus, Machine, SKU, RecipeVersion, RepositoryImageStatus
from app.production.schema import MachineRecipe, RecipeResponse, MachineResponse, SKUResponse, SKURecipe, RecipeVersionResponse
from app.storage.dependencies import get_storage_client

def to_machine_response(machine: Machine) -> MachineResponse:
    machine_recipes = [
        MachineRecipe(
            recipe_id=recipe.id, 
            recipe_code=recipe.recipe_code, 
            recipe_name=recipe.recipe_name, 
            sku_id=recipe.sku_id
        ) for recipe in machine.recipes
    ]
    dto = MachineResponse.model_validate(machine)
    dto.machine_recipes = machine_recipes

    return dto

def to_sku_response(sku: SKU) -> SKUResponse:
    sku_recipes = [
        SKURecipe(
            recipe_id=recipe.id, 
            recipe_code=recipe.recipe_code, 
            recipe_name=recipe.recipe_name, 
            machine_id=recipe.machine_id
        ) for recipe in sku.recipes
    ]
    dto = SKUResponse.model_validate(sku)
    dto.sku_recipes = sku_recipes
    return dto

def to_recipe_response(recipe: Recipe) -> RecipeResponse:
    dto = RecipeResponse.model_validate(recipe)
    released_recipe_version = next((rv for rv in recipe.recipe_versions if rv.status == RecipeVersionStatus.RELEASED), None)
    dto.current_released_version = released_recipe_version.version_code if released_recipe_version else None
    dto.sku_code = recipe.sku.sku_code
    dto.machine_code = recipe.machine.machine_code
    return dto

def to_recipe_version_response(recipe_version: RecipeVersion) -> RecipeVersionResponse:
    dto = RecipeVersionResponse.model_validate(recipe_version)
    dto.recipe_code = recipe_version.recipe.recipe_code if recipe_version.recipe else None
    return dto

def allow_recipe_version_status_transitions(
    current_status: RecipeVersionStatus, 
    new_status: RecipeVersionStatus, 
    approval_required: bool
) -> bool:
    if new_status == RecipeVersionStatus.SUPERSEDED:
        # superseded status is given by system, cannot be updated by user
        raise BadRequestError("Cannot update recipe version to superseded")

    if new_status == RecipeVersionStatus.DELETED:
        raise BadRequestError("Cannot update recipe version to deleted. Use delete recipe endpoint instead.")

    # if approval is required, only allow transition to released from approved
    if approval_required and new_status == RecipeVersionStatus.RELEASED:
        if new_status == RecipeVersionStatus.RELEASED and current_status == RecipeVersionStatus.APPROVED:
            return True
        else:
            raise BadRequestError(f"Approval is required to update recipe version from {current_status.value.lower()} to {new_status.value.lower()}")
    
    # if approval is not required, allow all transitions, both forward and backward
    return True

def is_recipe_version_immutable(status: RecipeVersionStatus) -> bool:
    return status in [RecipeVersionStatus.RELEASED, RecipeVersionStatus.OBSOLETE]


        