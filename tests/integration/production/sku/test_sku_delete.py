import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("seeded_skus")]

async def test_superadmin_delete_sku(authorized_client_superadmin):
    response = await authorized_client_superadmin.delete("/production/skus/TEST_SKU_00")
    assert response.status_code == 204
    response = await authorized_client_superadmin.get("/production/skus/TEST_SKU_00")
    assert response.status_code == 404
    assert response.json()["detail"] == "SKU with code TEST_SKU_00 not found"

async def test_admin_delete_sku(authorized_client_admin):
    response = await authorized_client_admin.delete("/production/skus/TEST_SKU_00")
    assert response.status_code == 204
    response = await authorized_client_admin.get("/production/skus/TEST_SKU_00")
    assert response.status_code == 404
    assert response.json()["detail"] == "SKU with code TEST_SKU_00 not found"

async def test_user_no_permission_delete_sku(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.delete("/production/skus/TEST_SKU_00")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access SKU_DELETE"

async def test_delete_sku_with_nonexistent_sku_code(authorized_client_admin):
    response = await authorized_client_admin.delete("/production/skus/TEST_SKU_55")
    assert response.status_code == 404
    assert response.json()["detail"] == "SKU with code TEST_SKU_55 not found"

async def test_delete_sku_with_deleted_status(authorized_client_admin):
    response = await authorized_client_admin.delete("/production/skus/TEST_SKU_00")
    assert response.status_code == 204
    response = await authorized_client_admin.delete("/production/skus/TEST_SKU_00")
    assert response.status_code == 404
    assert response.json()["detail"] == "SKU with code TEST_SKU_00 not found"

@pytest.mark.usefixtures("seeded_recipes")
async def test_delete_sku_with_recipes(authorized_client_admin):
    response = await authorized_client_admin.delete("/production/skus/TEST_SKU_00")
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot delete an SKU with recipes"