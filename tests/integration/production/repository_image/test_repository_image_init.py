import pytest
from app.core.config import settings
from tests.integration.production.repository_image.helpers import DRAFT_RECIPE_VERSION_CODE, RELEASED_CANDIDATE_VERSION_CODE

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.usefixtures("seeded_recipe_versions", "fake_storage"),
]

async def test_superadmin_init_repository_images(authorized_client_superadmin):
    response = await authorized_client_superadmin.post(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images/init",
        json={
            "images": [
                {
                    "original_filename": "ref1.jpg",
                    "content_type": "image/jpeg",
                },
                {
                    "original_filename": "ref2.png",
                    "content_type": "image/png",
                },
                {
                    "original_filename": "ref3.tiff",
                    "content_type": "image/tiff",
                },
            ],
        },
    )
    assert response.status_code == 201
    assert response.json()["recipe_version_id"] > 0
    assert len(response.json()["images"]) == 3
    assert response.json()["upload_expires_in_seconds"] > 0
    for image in response.json()["images"]:
        assert image["status"] == "Pending"
        assert image["upload_url"].startswith("http://fake-storage/upload/")
        assert image["bucket"]
        assert image["object_key"]

async def test_admin_init_repository_images(authorized_client_admin):
    response = await authorized_client_admin.post(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images/init",
        json={
            "images": [
                {
                    "original_filename": "ref1.webp",
                    "content_type": "image/webp",
                },
            ],
        },
    )
    assert response.status_code == 201


async def test_user_no_permission_init_repository_images(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.post(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images/init",
        json={
            "images": [
                {
                    "original_filename": "ref1.jpg",
                    "content_type": "image/jpeg",
                },
            ],
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access REPOSITORY_IMAGE_CREATE"

async def test_init_invalid_content_type(authorized_client_admin):
    response = await authorized_client_admin.post(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images/init",
        json={
            "images": [
                {
                    "original_filename": "ref1.pdf",
                    "content_type": "application/pdf",
                },
            ],
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Content type application/pdf is not allowed. Allowed content types are image/jpeg, image/png, image/webp, image/tiff"

async def test_init_recipe_version_not_found(authorized_client_admin):
    response = await authorized_client_admin.post(
        f"/production/recipe-versions/1/repository-images/init",
        json={
            "images": [
                {
                    "original_filename": "ref1.jpg",
                    "content_type": "image/jpeg",
                },
            ],
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe version with code 1 not found"

async def test_init_on_released_recipe_version(authorized_client_admin):
    #TEST_RECIPE_VERSION_002 has approval_required=False -> can release from Draft directly
    response = await authorized_client_admin.patch(
        f"/production/recipe-versions/{RELEASED_CANDIDATE_VERSION_CODE}",
        json={
            "status": "Released",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Released"

    response = await authorized_client_admin.post(
        f"/production/recipe-versions/{RELEASED_CANDIDATE_VERSION_CODE}/repository-images/init",
        json={
            "images": [
                {
                    "original_filename": "ref1.jpg",
                    "content_type": "image/jpeg",
                },
            ],
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot init repository images for a released recipe version"

async def test_init_max_repository_images_per_recipe_version(authorized_client_admin):
    # Add more than max allowed repository images in one request. Should fail with 422.
    response = await authorized_client_admin.post(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images/init",
        json={
            "images": [
                {
                    "original_filename": f"ref{i}.jpg",
                    "content_type": "image/jpeg",
                }
                for i in range(0, settings.MAX_REPOSITORY_IMAGES_PER_RECIPE_VERSION+1)
            ],
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Value error, Maximum repository images per recipe version is 100. You are trying to add 101 repository images for field images"

    # add images less than max allowed repository images in one request. Should succeed with 201.
    response = await authorized_client_admin.post(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images/init",
        json={
            "images": [
                {
                    "original_filename": f"ref{i}.jpg",
                    "content_type": "image/jpeg",
                }
                for i in range(0, settings.MAX_REPOSITORY_IMAGES_PER_RECIPE_VERSION - 1)
            ],
        },
    )
    assert response.status_code == 201
    assert len(response.json()["images"]) == 99

    # get repository images. Should succeed with 200 with 99 repository images.
    response = await authorized_client_admin.get(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images?limit=100",
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 99

    # add more images, less than max allowed in one request but will exceed max allowed in total. Should fail with 400.
    response = await authorized_client_admin.post(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images/init",
        json={
            "images": [
                {
                    "original_filename": f"ref10{i}.jpg",
                    "content_type": "image/jpeg",
                } for i in range(0, 2)
            ],
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Maximum repository images per recipe version is 100. You can only add up to 1 more repository images"

    # add one more image, exactly max allowed in one request. Should succeed with 201.
    response = await authorized_client_admin.post(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images/init",
        json={
            "images": [
                {
                    "original_filename": f"ref100.jpg",
                    "content_type": "image/jpeg",
                } 
            ],
        },
    )
    assert response.status_code == 201
    assert len(response.json()["images"]) == 1

    # get repository images. Should succeed with 200 with 100 repository images.
    response = await authorized_client_admin.get(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images?limit=100",
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 100

async def test_init_repository_images_with_same_original_filename(authorized_client_admin):
    # Add two repository images with the same original filename. 
    # Should succeed with 201. because repository image key is unique with uuid
    response = await authorized_client_admin.post(
        f"/production/recipe-versions/{DRAFT_RECIPE_VERSION_CODE}/repository-images/init",
        json={
            "images": [
                {
                    "original_filename": "ref1.jpg",
                    "content_type": "image/jpeg",
                },

                {
                    "original_filename": "ref1.jpg",
                    "content_type": "image/jpeg",
                },
            ],
        },
    )
    assert response.status_code == 201
    assert len(response.json()["images"]) == 2

