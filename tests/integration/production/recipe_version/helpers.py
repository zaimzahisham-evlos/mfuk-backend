"""
Shared steps for recipe version tests.
"""
from httpx import AsyncClient, Response

RELEASED_CANDIDATE_VERSION_CODE = "TEST_RECIPE_VERSION_002"  # approval_required=False

async def release_recipe_version(client: AsyncClient, version_code: str = RELEASED_CANDIDATE_VERSION_CODE) -> None:
    response = await client.patch(
        f"/production/recipe-versions/{version_code}",
        json={"status": "Released"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "Released"