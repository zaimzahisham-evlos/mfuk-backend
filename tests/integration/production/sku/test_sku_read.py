import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("seeded_skus")]

async def test_superadmin_get_all_skus(authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/production/skus")
    assert response.status_code == 200
    assert len(response.json()) == 2

async def test_admin_get_all_skus(authorized_client_admin):
    response = await authorized_client_admin.get("/production/skus")
    assert response.status_code == 200
    assert len(response.json()) == 2

async def test_user_no_permission_get_all_skus(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.get("/production/skus")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access SKU_VIEW"

async def test_get_skus_with_statuses(authorized_client_admin):
    response = await authorized_client_admin.get("/production/skus?statuses=Active")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["sku_code"] == "TEST_SKU_00"
    assert response.json()[0]["sku_name"] == "Test SKU 00"
    assert response.json()[0]["status"] == "Active"
    
    response = await authorized_client_admin.get("/production/skus?statuses=Inactive")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["sku_code"] == "TEST_SKU_99"
    assert response.json()[0]["sku_name"] == "Test SKU 99"
    assert response.json()[0]["status"] == "Inactive"

async def test_get_skus_with_multiple_statuses(authorized_client_admin):
    response = await authorized_client_admin.get("/production/skus?statuses=Active&statuses=Inactive")
    assert response.status_code == 200
    assert len(response.json()) == 2

async def test_get_skus_with_deleted(authorized_client_admin):
    # get all skus
    response = await authorized_client_admin.get("/production/skus")
    assert response.status_code == 200
    assert len(response.json()) == 2

    # delete one sku
    sku = response.json()[0]
    response = await authorized_client_admin.delete(f"/production/skus/{sku['sku_code']}")
    assert response.status_code == 204

    # get all skus without include_deleted
    response = await authorized_client_admin.get("/production/skus")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # get all skus with include_deleted
    response = await authorized_client_admin.get("/production/skus?include_deleted=true")
    assert response.status_code == 200
    assert len(response.json()) == 2

    # get all skus with include_deleted and statuses=Deleted
    response = await authorized_client_admin.get("/production/skus?include_deleted=true&statuses=Deleted")
    assert response.status_code == 200
    assert len(response.json()) == 1

async def test_get_sku_by_sku_code(authorized_client_superadmin):
    response = await authorized_client_superadmin.get("/production/skus/TEST_SKU_00")
    assert response.status_code == 200
    assert response.json()["sku_code"] == "TEST_SKU_00"
    assert response.json()["sku_name"] == "Test SKU 00"
    assert response.json()["status"] == "Active"
    
async def test_get_sku_by_code_not_found(authorized_client_admin):
    response = await authorized_client_admin.get("/production/skus/TEST_SKU_55")
    assert response.status_code == 404
    assert response.json()["detail"] == "SKU with code TEST_SKU_55 not found"

async def test_user_no_permission_get_sku_by_sku_code(authorized_client_human_no_role):
    response = await authorized_client_human_no_role.get("/production/skus/TEST_SKU_00")
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have permission to access SKU_VIEW"

async def test_get_sku_by_code_deleted(authorized_client_admin):
    response = await authorized_client_admin.get("/production/skus/TEST_SKU_99")
    assert response.status_code == 200
    assert response.json()["sku_code"] == "TEST_SKU_99"
    assert response.json()["sku_name"] == "Test SKU 99"
    assert response.json()["status"] == "Inactive"
    response = await authorized_client_admin.delete(f"/production/skus/TEST_SKU_99")
    assert response.status_code == 204
    response = await authorized_client_admin.get("/production/skus/TEST_SKU_99")
    assert response.status_code == 404
    assert response.json()["detail"] == "SKU with code TEST_SKU_99 not found"

